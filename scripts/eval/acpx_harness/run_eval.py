#!/usr/bin/env python3
"""
Docker-based eval harness for comparing claude_code and cursor_composer2 agents
on GEOS XML authoring tasks via acpx.

Usage:
    # Run all tasks for both agents under experiment_run1
    python run_eval.py --run experiment_run1

    # Specific agents only
    python run_eval.py --run experiment_run1 --agents claude_code

    # Include only specific tasks
    python run_eval.py --run experiment_run1 --include TutorialDeadOilEgg ExampleEDPWellbore

    # Exclude specific tasks
    python run_eval.py --run experiment_run1 --exclude TutorialDeadOilEgg

    # Override the experiments source directory
    python run_eval.py --run experiment_run1 --experiments-dir /path/to/my/tasks

    # Dry run (prints docker commands without executing)
    python run_eval.py --run experiment_run1 --dry-run

    # Adjust concurrency and timeout
    python run_eval.py --run experiment_run1 --workers 4 --timeout 900

Build the Docker image first:
    docker build -t geos-eval scripts/eval/acpx_harness/

Expected layout after a run:
    /home/brianliu/data/eval/
    ├── claude_code/
    │   └── experiment_run1/
    │       └── <task>/
    │           ├── inputs/          ← agent-generated XML files
    │           ├── outputs/         ← agent-generated outputs
    │           ├── acpx_output.json ← stdout from acpx
    │           ├── stderr.txt       ← stderr from acpx
    │           └── exit_code.txt    ← process exit code
    └── cursor_composer2/
        └── experiment_run1/
            └── <task>/
                └── ...

To evaluate results afterwards, use batch_lxml_evaluate.py:
    uv run python scripts/eval/batch_lxml_evaluate.py \\
        --experiments-dir /home/brianliu/data/eval/claude_code/experiment_run1 \\
        --ground-truth-dir /home/brianliu/data/eval/experiments_gt \\
        --results-dir /home/brianliu/data/eval/claude_code_results/experiment_run1
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
EXPERIMENTS_DIR = Path("/home/brianliu/data/eval/experiments")
GEOS_LIB_DIR = Path("/home/brianliu/data/GEOS")
DOCKER_IMAGE = "geos-eval"

# ---------------------------------------------------------------------------
# Agent definitions
# acpx_name: the agent identifier passed to `acpx <agent> exec`
# results_dir: where per-task workspaces land on the host
# api_key_env: environment variable name for the agent's API key
# ---------------------------------------------------------------------------

AGENTS: dict[str, dict] = {
    "claude_code": {
        "acpx_name": "claude",
        "results_dir": Path("/home/brianliu/data/eval/claude_code"),
        "api_key_env": "ANTHROPIC_API_KEY",
        "model": None,  # passed via ANTHROPIC_API_KEY; model set by claude itself
    },
    "cursor_composer2": {
        "acpx_name": "cursor",
        "results_dir": Path("/home/brianliu/data/eval/cursor_composer2"),
        "api_key_env": "CURSOR_API_KEY",
        "model": "composer-2",
    },
}

DEFAULT_TIMEOUT = 600  # seconds per task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_agents_md() -> str:
    path = SCRIPT_DIR / "AGENTS.md"
    if not path.exists():
        raise FileNotFoundError(f"AGENTS.md not found at {path}")
    return path.read_text()


def load_task_instructions(task_dir: Path) -> str:
    path = task_dir / "instructions.txt"
    if not path.exists():
        raise FileNotFoundError(f"instructions.txt not found in {task_dir}")
    return path.read_text()


def build_prompt(agents_context: str, task_instructions: str) -> str:
    return (
        f"{agents_context}\n\n"
        "--- BEGIN SIMULATION SPECIFICATION ---\n"
        f"{task_instructions.strip()}\n"
        "--- END SIMULATION SPECIFICATION ---"
    )


# ---------------------------------------------------------------------------
# Per-task runner
# ---------------------------------------------------------------------------

def run_task(
    task_name: str,
    agent_key: str,
    agents_context: str,
    experiments_dir: Path,
    run_name: str,
    timeout: int,
    dry_run: bool,
) -> dict:
    agent = AGENTS[agent_key]
    task_dir = experiments_dir / task_name
    result_dir = agent["results_dir"] / run_name / task_name

    # Ensure workspace subdirs exist on the host before mounting
    (result_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (result_dir / "outputs").mkdir(parents=True, exist_ok=True)

    task_instructions = load_task_instructions(task_dir)
    prompt = build_prompt(agents_context, task_instructions)

    model = agent.get("model")
    api_key = os.environ.get(agent["api_key_env"], "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    # For cursor: prepend /model slash command as the most reliable way to set
    # the model within an acpx session (Cursor ACP doesn't advertise models yet).
    if model and agent["acpx_name"] == "cursor":
        prompt = f"/model {model}\n\n{prompt}"

    extra_env: list[str] = []
    # Also pass CURSOR_MODEL env var in case the cursor CLI honours it at startup.
    if model and agent["acpx_name"] == "cursor":
        extra_env = ["-e", f"CURSOR_MODEL={model}"]

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{GEOS_LIB_DIR}:/geos_lib:ro",
        "-v", f"{result_dir}:/workspace:rw",
        "-e", f"{agent['api_key_env']}={api_key}",
        "-e", f"ANTHROPIC_API_KEY={anthropic_key}",
        *extra_env,
        DOCKER_IMAGE,
        "acpx",
        "--approve-reads",
        "--format", "json",
        "--cwd", "/workspace",
        agent["acpx_name"],
        "exec", prompt,
    ]

    if dry_run:
        # Print a truncated command for inspection
        display = " ".join(cmd[:12]) + " ..."
        print(f"  [DRY RUN] {display}")
        return {"task": task_name, "agent": agent_key, "status": "dry_run"}

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        (result_dir / "acpx_output.json").write_text(proc.stdout)
        (result_dir / "stderr.txt").write_text(proc.stderr)
        (result_dir / "exit_code.txt").write_text(str(proc.returncode))

        status = "success" if proc.returncode == 0 else "failed"
        return {
            "task": task_name,
            "agent": agent_key,
            "status": status,
            "exit_code": proc.returncode,
        }

    except subprocess.TimeoutExpired:
        (result_dir / "exit_code.txt").write_text("timeout")
        (result_dir / "stderr.txt").write_text(f"Timed out after {timeout}s")
        return {"task": task_name, "agent": agent_key, "status": "timeout"}

    except Exception as exc:
        (result_dir / "exit_code.txt").write_text("error")
        (result_dir / "stderr.txt").write_text(str(exc))
        return {"task": task_name, "agent": agent_key, "status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

class C:
    GREEN   = "\033[92m"
    WARNING = "\033[93m"
    FAIL    = "\033[91m"
    CYAN    = "\033[96m"
    BOLD    = "\033[1m"
    HEADER  = "\033[95m"
    ENDC    = "\033[0m"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GEOS eval harness: runs claude_code and cursor_composer2 via Docker + acpx",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--run", "-r",
        required=True,
        metavar="RUN_NAME",
        help="Name of the experiment run subfolder, e.g. experiment_run1. "
             "Results land at <agent_dir>/<run>/<task>/",
    )
    parser.add_argument(
        "--experiments-dir", "-d",
        type=Path,
        default=EXPERIMENTS_DIR,
        help=f"Directory containing task subdirs with instructions.txt "
             f"(default: {EXPERIMENTS_DIR})",
    )
    parser.add_argument(
        "--agents", "-a",
        nargs="+",
        choices=list(AGENTS.keys()),
        default=list(AGENTS.keys()),
        help="Agents to evaluate (default: all)",
    )
    parser.add_argument(
        "--include", "-i",
        nargs="+",
        metavar="TASK_NAME",
        help="Run only these tasks (default: all tasks in experiments dir)",
    )
    parser.add_argument(
        "--exclude", "-x",
        nargs="+",
        metavar="TASK_NAME",
        default=[],
        help="Skip these tasks (applied after --include)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout per task in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=2,
        help="Max concurrent docker runs (default: 2; keep low to avoid OOM)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print docker commands without executing",
    )
    args = parser.parse_args()

    experiments_dir: Path = args.experiments_dir

    # Validate experiments directory
    if not experiments_dir.exists():
        print(f"{C.FAIL}Error: experiments dir not found: {experiments_dir}{C.ENDC}")
        sys.exit(1)

    # Discover all tasks
    all_tasks = sorted(d.name for d in experiments_dir.iterdir() if d.is_dir())

    # Apply --include filter
    if args.include:
        missing = [t for t in args.include if t not in all_tasks]
        if missing:
            print(f"{C.WARNING}Warning: tasks not found in {experiments_dir}: {missing}{C.ENDC}")
        tasks = [t for t in args.include if t in all_tasks]
    else:
        tasks = all_tasks

    # Apply --exclude filter
    if args.exclude:
        excluded = set(args.exclude)
        tasks = [t for t in tasks if t not in excluded]

    if not tasks:
        print(f"{C.FAIL}No tasks to run.{C.ENDC}")
        sys.exit(1)

    agents_context = load_agents_md()
    combos = [(task, agent) for task in tasks for agent in args.agents]

    # Show where results will land
    result_paths = {
        agent_key: AGENTS[agent_key]["results_dir"] / args.run
        for agent_key in args.agents
    }

    print(f"\n{C.BOLD}{C.HEADER}{'=' * 70}{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}  GEOS Eval Harness{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}{'=' * 70}{C.ENDC}")
    print(f"  Run name       : {args.run}")
    print(f"  Experiments dir: {experiments_dir}")
    print(f"  Tasks          : {len(tasks)}")
    print(f"  Agents         : {args.agents}")
    print(f"  Combos         : {len(combos)}")
    print(f"  Timeout        : {args.timeout}s per task")
    print(f"  Workers        : {args.workers}")
    print(f"  Dry run        : {args.dry_run}")
    for agent_key, path in result_paths.items():
        print(f"  Results ({agent_key}): {path}")
    print(f"  Started        : {datetime.now().isoformat()}")
    print(f"{C.BOLD}{C.HEADER}{'=' * 70}{C.ENDC}\n")

    results: list[dict] = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                run_task, task, agent, agents_context,
                experiments_dir, args.run, args.timeout, args.dry_run
            ): (task, agent)
            for task, agent in combos
        }
        for i, future in enumerate(as_completed(futures), 1):
            task, agent = futures[future]
            try:
                result = future.result()
                results.append(result)
                status = result.get("status", "?")
                color = C.GREEN if status == "success" else (C.WARNING if status == "dry_run" else C.FAIL)
                print(f"[{i:3d}/{len(combos)}] {color}{status:<8}{C.ENDC}  {agent:<20}  {task}")
            except Exception as exc:
                results.append({"task": task, "agent": agent, "status": "error", "error": str(exc)})
                print(f"[{i:3d}/{len(combos)}] {C.FAIL}ERROR   {C.ENDC}  {agent:<20}  {task}  ({exc})")

    # Summary
    succeeded = sum(1 for r in results if r["status"] == "success")
    failed    = sum(1 for r in results if r["status"] not in ("success", "dry_run"))
    print(f"\n{C.BOLD}Done{C.ENDC}: {C.GREEN}{succeeded} succeeded{C.ENDC}, "
          f"{C.FAIL}{failed} failed{C.ENDC} / {len(combos)} total")

    if failed:
        print(f"\n{C.FAIL}Failed tasks:{C.ENDC}")
        for r in results:
            if r["status"] not in ("success", "dry_run"):
                print(f"  [{r['status']}] {r['agent']} / {r['task']}"
                      + (f": {r.get('error', '')}" if r.get("error") else ""))


if __name__ == "__main__":
    main()
