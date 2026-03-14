#!/usr/bin/env python3
"""
Run GEOS agent evaluation experiments concurrently without the run_geos tool.

This script mirrors run_experiments_parallel.py, but each agent process is
constructed with the default tool set minus run_geos so the model cannot invoke
simulation execution during the experiment.

Usage:
    uv run python scripts/eval/run_experiments_no_geos_parallel.py
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


DEFAULT_EVAL_PREAMBLE = """\
You are being evaluated on your ability to author GEOS XML input files from \
a natural language specification. Use the documentation search tools \
(search_navigator, search_technical, search_schema) to learn GEOS XML syntax \
and patterns, then author the configuration files yourself. You can read files \
with read_file or grep_search and modify them with write_file or edit_file. \
If a tool blocks access to a file, move on and rely on documentation search instead.

You do not have access to simulation execution tools in this evaluation run.
Do not try to run GEOS; author the best XML inputs directly from the spec and docs.

--- BEGIN SIMULATION SPECIFICATION ---
"""

EXCLUDED_GT_XML_FILENAMES_ENV = "EXCLUDED_GT_XML_FILENAMES"

NO_GEOS_AGENT_CODE = r"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

from geos_agent.agent_config import AgentConfig
from geos_agent.geos_agent import AgentTerminationException, GeosAgent
from geos_agent.tools.utils import build_default_tools


EXCLUDED_GT_XML_FILENAMES_ENV = "EXCLUDED_GT_XML_FILENAMES"


def save_log(agent: GeosAgent, log_path: str) -> None:
    log_data = agent._get_conversation_log()
    log_file = Path(log_path).resolve()
    with log_file.open("w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)


def sanitize_system_prompt(prompt: str) -> str:
    prompt = re.sub(
        r"\nEXECUTION REQUIREMENTS:\n(?:  • .*\n)+",
        "\nEXECUTION REQUIREMENTS:\n"
        "  • Simulation execution is unavailable in this run.\n"
        "  • Do not attempt to run GEOS or rely on execution feedback.\n"
        "  • Focus on producing the best possible XML inputs directly from the specification and documentation.\n",
        prompt,
        count=1,
    )
    prompt = re.sub(
        r"\n  `run_geos`:\n(?:  • .*\n(?:    - .*\n)*)+",
        "\n",
        prompt,
        count=1,
    )
    prompt = prompt.replace(
        "4. Run GEOS, inspect logs/output, and refine as needed\n",
        "4. Validate the XML structure and assumptions from documentation instead of running GEOS\n",
    )
    return prompt


def load_blocked_gt_xml_filenames() -> set[str]:
    raw = os.environ.get(EXCLUDED_GT_XML_FILENAMES_ENV, "").strip()
    if not raw:
        return set()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return set()
    if not isinstance(data, list):
        return set()
    return {
        str(name).strip().lower()
        for name in data
        if str(name).strip().lower().endswith(".xml")
    }


def is_blocked_xml_path(path: str, blocked_xml_filenames: set[str]) -> bool:
    if not blocked_xml_filenames:
        return False
    candidate = Path(path)
    return candidate.suffix.lower() == ".xml" and candidate.name.lower() in blocked_xml_filenames


def restrict_xml_access(tools: list, blocked_xml_filenames: set[str]) -> None:
    if not blocked_xml_filenames:
        return

    for tool in tools:
        if tool.name == "read_file":
            original_run = tool.run

            def read_file_run(
                path: str,
                max_chars: int = 4000,
                start_line: int | None = None,
                end_line: int | None = None,
                start_marker: str | None = None,
                end_marker: str | None = None,
            ):
                if is_blocked_xml_path(path, blocked_xml_filenames):
                    return {
                        "error": (
                            "Access denied: XML files whose names match this "
                            "experiment's ground-truth XML set are restricted."
                        ),
                        "path": path,
                    }
                return original_run(
                    path=path,
                    max_chars=max_chars,
                    start_line=start_line,
                    end_line=end_line,
                    start_marker=start_marker,
                    end_marker=end_marker,
                )

            tool.run = read_file_run

        elif tool.name == "grep_search":
            original_run = tool.run

            def grep_search_run(regex_pattern: str, directory: str = "./"):
                result = original_run(regex_pattern=regex_pattern, directory=directory)
                if "results" not in result:
                    return result
                filtered_results = [
                    item
                    for item in result["results"]
                    if not is_blocked_xml_path(str(item.get("filepath", "")), blocked_xml_filenames)
                ]
                result["results"] = filtered_results
                result["count"] = len(filtered_results)
                return result

            tool.run = grep_search_run

        elif tool.name == "search_technical":
            original_run = tool.run

            def search_technical_run(query: str, n_results: int = 5):
                result = original_run(query=query, n_results=n_results)
                if "results" not in result:
                    return result
                result["results"] = [
                    item
                    for item in result["results"]
                    if not is_blocked_xml_path(str(item.get("xml_reference") or ""), blocked_xml_filenames)
                    and not is_blocked_xml_path(str(item.get("source_path") or ""), blocked_xml_filenames)
                ]
                return result

            tool.run = search_technical_run


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run GEOS-Agent with run_geos removed from the tool set."
    )
    parser.add_argument("--instruction", required=True, type=str)
    parser.add_argument("--workspace", default=".", type=str)
    parser.add_argument("--log", default=None, type=str)
    parser.add_argument("--model", default="moonshotai/kimi-k2.5", type=str)
    parser.add_argument("--max-steps", default=100, type=int)
    parser.add_argument("--max-retries", default=3, type=int)
    parser.add_argument("--retry-delay", default=1.0, type=float)
    parser.add_argument("--retry-backoff", default=2.0, type=float)
    parser.add_argument("--no-cheatsheet", action="store_true")
    parser.add_argument("--no-curate", action="store_true")
    parser.add_argument("--curator-model", default=None, type=str)
    parser.add_argument("--disable-context-pruning", action="store_true")
    parser.add_argument("--context-pruning-manual", action="store_true")
    parser.add_argument("--context-limit", default=100000, type=int)
    parser.add_argument("--disable-compress-tool", action="store_true")
    parser.add_argument("--disable-prompt-caching", action="store_true")
    parser.add_argument("--prompt-cache-ttl", choices=("default", "1h"), default="default")
    args = parser.parse_args()

    workspace_root = Path(args.workspace).resolve()
    blocked_xml_filenames = load_blocked_gt_xml_filenames()
    disabled_tools = {"run_geos", "run_shell", "run_python_code"}
    tools = [tool for tool in build_default_tools(workspace_root) if tool.name not in disabled_tools]
    restrict_xml_access(tools, blocked_xml_filenames)

    config = AgentConfig(
        model=args.model,
        max_steps=args.max_steps,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        retry_backoff=args.retry_backoff,
        include_cheatsheet=not args.no_cheatsheet,
        curate_cheatsheet=not args.no_cheatsheet and not args.no_curate,
        curator_model=args.curator_model,
    )
    config.context_pruning.enabled = not args.disable_context_pruning
    config.context_pruning.manual_mode.enabled = args.context_pruning_manual
    config.context_pruning.tools.settings.context_limit = max(0, args.context_limit)
    config.openrouter_prompt_caching = not args.disable_prompt_caching
    config.openrouter_prompt_cache_ttl = None if args.prompt_cache_ttl == "default" else args.prompt_cache_ttl
    if args.disable_compress_tool:
        config.context_pruning.tools.compress.permission = "deny"

    agent = GeosAgent(
        workspace_root=workspace_root,
        tools=tools,
        config=config,
    )
    agent.system_prompt = sanitize_system_prompt(agent.system_prompt)

    try:
        agent.run(args.instruction)
        if args.log:
            save_log(agent, args.log)
    except AgentTerminationException as exc:
        print(str(exc), file=sys.stderr)
        if args.log:
            try:
                save_log(agent, args.log)
            except Exception as log_error:  # noqa: BLE001
                print(f"Failed to save conversation log: {log_error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
"""


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def get_project_root() -> Path:
    """Get project root directory."""
    script_dir = Path(__file__).parent
    return (script_dir / "../..").resolve()


def collect_ground_truth_xml_filenames(gt_experiment_dir: Path) -> List[str]:
    """Collect all XML basenames under one ground-truth experiment directory."""
    if not gt_experiment_dir.exists():
        return []
    return sorted({path.name.lower() for path in gt_experiment_dir.rglob("*.xml") if path.is_file()})


def build_experiment_env(
    experiment_name: str,
    ground_truth_dir: Path,
    base_env: Dict[str, str] | None = None,
) -> Tuple[Dict[str, str], Path, List[str]]:
    """Build subprocess env vars that prevent XML leakage for one experiment."""
    env = dict(base_env or os.environ.copy())
    gt_experiment_dir = ground_truth_dir / experiment_name
    blocked_xml_filenames = collect_ground_truth_xml_filenames(gt_experiment_dir)
    env[EXCLUDED_GT_XML_FILENAMES_ENV] = json.dumps(blocked_xml_filenames)
    return env, gt_experiment_dir, blocked_xml_filenames


async def run_experiment(
    experiment_dir: Path,
    ground_truth_dir: Path,
    log_dir: Path,
    semaphore: asyncio.Semaphore,
    experiment_name: str,
    model: str,
    max_steps: int,
    max_retries: int,
    retry_delay: float,
    retry_backoff: float,
    jsonl_log_dir: Path = None,
    eval_preamble: str = None,
) -> Tuple[str, bool, float]:
    """Run a single experiment and return (name, success, duration_seconds)."""
    async with semaphore:
        instructions_file = experiment_dir / "instructions.txt"
        log_file = log_dir / f"{experiment_name}.log"

        if not instructions_file.exists():
            error_msg = f"instructions.txt not found in {experiment_dir}"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"ERROR: {error_msg}\n")
            print(f"{Colors.FAIL}✗ {experiment_name}: {error_msg}{Colors.ENDC}")
            return (experiment_name, False, 0.0)

        instructions = instructions_file.read_text(encoding="utf-8").strip()
        if eval_preamble:
            instructions = eval_preamble.strip() + "\n\n" + instructions

        cmd = [
            "uv", "run", "python", "-c", NO_GEOS_AGENT_CODE,
            "--instruction", instructions,
            "--workspace", str(experiment_dir),
            "--model", model,
            "--max-steps", str(max_steps),
            "--max-retries", str(max_retries),
            "--retry-delay", str(retry_delay),
            "--retry-backoff", str(retry_backoff),
        ]

        if jsonl_log_dir:
            jsonl_log_file = jsonl_log_dir / f"{experiment_name}.jsonl"
            cmd.extend(["--log", str(jsonl_log_file)])

        print(f"{Colors.OKCYAN}▶ Starting: {experiment_name}{Colors.ENDC}")
        start_time = asyncio.get_event_loop().time()

        try:
            with open(log_file, "w", encoding="utf-8") as f:
                env, gt_experiment_dir, blocked_xml_filenames = build_experiment_env(
                    experiment_name=experiment_name,
                    ground_truth_dir=ground_truth_dir,
                )
                f.write(f"{'=' * 80}\n")
                f.write(f"Experiment: {experiment_name}\n")
                f.write(f"Started: {datetime.now().isoformat()}\n")
                f.write(f"Workspace: {experiment_dir}\n")
                f.write(f"Ground truth: {gt_experiment_dir}\n")
                f.write(f"Model: {model}\n")
                f.write(f"Max steps: {max_steps}\n")
                f.write("Runner mode: no run_geos tool\n")
                f.write("Disabled tools: run_geos, run_shell, run_python_code\n")
                f.write(f"Blocked GT XML basenames ({len(blocked_xml_filenames)}): ")
                f.write(json.dumps(blocked_xml_filenames))
                f.write("\n")
                f.write(f"Command: {json.dumps(cmd)}\n")
                f.write(f"{'=' * 80}\n\n")
                f.flush()

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=get_project_root(),
                    env=env,
                )
                returncode = await process.wait()

            duration = asyncio.get_event_loop().time() - start_time
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 80}\n")
                f.write(f"Completed: {datetime.now().isoformat()}\n")
                f.write(f"Duration: {duration:.2f}s\n")
                f.write(f"Return code: {returncode}\n")
                f.write(f"{'=' * 80}\n")

            if returncode == 0:
                print(f"{Colors.OKGREEN}✓ Completed: {experiment_name} ({duration:.2f}s){Colors.ENDC}")
                return (experiment_name, True, duration)

            print(f"{Colors.FAIL}✗ Failed: {experiment_name} (exit code {returncode}){Colors.ENDC}")
            return (experiment_name, False, duration)

        except Exception as exc:  # noqa: BLE001
            duration = asyncio.get_event_loop().time() - start_time
            error_msg = f"Exception: {exc}"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 80}\n")
                f.write(f"ERROR: {error_msg}\n")
                f.write(f"{'=' * 80}\n")
            print(f"{Colors.FAIL}✗ Error: {experiment_name}: {error_msg}{Colors.ENDC}")
            return (experiment_name, False, duration)


async def run_all_experiments(
    experiments_dir: Path,
    ground_truth_dir: Path,
    log_dir: Path,
    max_workers: int,
    model: str,
    max_steps: int,
    max_retries: int,
    retry_delay: float,
    retry_backoff: float,
    jsonl_log_dir: Path = None,
    experiment_filter: List[str] = None,
    eval_preamble: str = None,
):
    """Run all experiments concurrently with limited parallelism."""
    experiment_dirs = [
        d for d in experiments_dir.iterdir()
        if d.is_dir() and (experiment_filter is None or d.name in experiment_filter)
    ]

    if not experiment_dirs:
        print(f"{Colors.WARNING}No experiments found in {experiments_dir}{Colors.ENDC}")
        return

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}GEOS Agent Parallel Experiment Runner (No run_geos){Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"Experiments: {len(experiment_dirs)}")
    print(f"Max workers: {max_workers}")
    print(f"Model: {model}")
    print(f"Max steps: {max_steps}")
    print(f"Ground truth directory: {ground_truth_dir}")
    print(f"Stdout/stderr logs: {log_dir}")
    if jsonl_log_dir:
        print(f"JSONL conversation logs: {jsonl_log_dir}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")

    semaphore = asyncio.Semaphore(max_workers)
    tasks = [
        run_experiment(
            exp_dir,
            ground_truth_dir,
            log_dir,
            semaphore,
            exp_dir.name,
            model,
            max_steps,
            max_retries,
            retry_delay,
            retry_backoff,
            jsonl_log_dir,
            eval_preamble,
        )
        for exp_dir in experiment_dirs
    ]

    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    total_duration = asyncio.get_event_loop().time() - start_time

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}Summary{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")

    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    print(f"Total experiments: {len(results)}")
    print(f"{Colors.OKGREEN}Successful: {len(successful)}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {len(failed)}{Colors.ENDC}")
    print(f"Total time: {total_duration:.2f}s")

    if successful:
        avg_duration = sum(r[2] for r in successful) / len(successful)
        print(f"Avg duration (successful): {avg_duration:.2f}s")

    if failed:
        print(f"\n{Colors.FAIL}Failed experiments:{Colors.ENDC}")
        for name, _, duration in failed:
            print(f"  - {name} ({duration:.2f}s)")

    print(f"\n{Colors.OKBLUE}Logs saved to: {log_dir}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")

    if failed:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Run GEOS agent experiments in parallel without run_geos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=4,
        help="Number of concurrent workers (default: 4)",
    )
    parser.add_argument(
        "--experiments-dir",
        type=Path,
        default=None,
        help="Path to experiments directory (default: data/eval/experiments_subset)",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=None,
        help="Path to stdout/stderr logs directory (default: data/eval/logs)",
    )
    parser.add_argument(
        "--jsonl-log-dir",
        type=Path,
        default=None,
        help="Path to JSONL conversation logs directory (default: none, no JSONL logs)",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=Path,
        default=None,
        help="Path to ground-truth experiments directory (default: data/eval/experiments_gt)",
    )
    parser.add_argument(
        "--experiments",
        "-e",
        nargs="+",
        help="Specific experiments to run (default: all)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="moonshotai/kimi-k2.5",
        help="OpenRouter model name (default: moonshotai/kimi-k2.5)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=100,
        help="Maximum agent-tool iterations (default: 100)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum API retry attempts (default: 3)",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        help="Initial delay between retries in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=2.0,
        help="Exponential backoff multiplier for retry delays (default: 2.0)",
    )
    parser.add_argument(
        "--no-eval-preamble",
        action="store_true",
        help="Disable the default eval preamble that prevents GT leakage via instructions",
    )
    parser.add_argument(
        "--eval-preamble",
        type=str,
        default=None,
        help="Custom eval preamble text (overrides the default)",
    )

    args = parser.parse_args()

    project_root = get_project_root()
    experiments_dir = args.experiments_dir or project_root / "data/eval/experiments_subset"
    ground_truth_dir = args.ground_truth_dir or project_root / "data/eval/experiments_gt"
    log_dir = args.log_dir or project_root / "data/eval/logs"

    if not experiments_dir.exists():
        print(f"{Colors.FAIL}Error: Experiments directory not found: {experiments_dir}{Colors.ENDC}")
        sys.exit(1)
    if not ground_truth_dir.exists():
        print(f"{Colors.FAIL}Error: Ground-truth directory not found: {ground_truth_dir}{Colors.ENDC}")
        sys.exit(1)

    log_dir.mkdir(parents=True, exist_ok=True)
    if args.jsonl_log_dir:
        args.jsonl_log_dir.mkdir(parents=True, exist_ok=True)

    if args.no_eval_preamble:
        eval_preamble = None
    elif args.eval_preamble:
        eval_preamble = args.eval_preamble
    else:
        eval_preamble = DEFAULT_EVAL_PREAMBLE

    asyncio.run(
        run_all_experiments(
            experiments_dir=experiments_dir,
            ground_truth_dir=ground_truth_dir,
            log_dir=log_dir,
            max_workers=args.workers,
            model=args.model,
            max_steps=args.max_steps,
            max_retries=args.max_retries,
            retry_delay=args.retry_delay,
            retry_backoff=args.retry_backoff,
            jsonl_log_dir=args.jsonl_log_dir,
            experiment_filter=args.experiments,
            eval_preamble=eval_preamble,
        )
    )


if __name__ == "__main__":
    main()
