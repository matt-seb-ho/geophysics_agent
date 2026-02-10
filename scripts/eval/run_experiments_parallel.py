#!/usr/bin/env python3
"""
Run GEOS agent evaluation experiments concurrently (data parallel).

This script runs multiple experiments in parallel, each with its own:
- instructions.txt file
- workspace directory
- stdout/stderr log file
- optional JSONL conversation log file

Usage:
    # Run with default concurrency (4 workers)
    uv run python scripts/eval/run_experiments_parallel.py

    # Run with custom concurrency and model
    uv run python scripts/eval/run_experiments_parallel.py --workers 8 --model "anthropic/claude-3.5-sonnet"

    # Run specific experiments with JSONL logs
    uv run python scripts/eval/run_experiments_parallel.py \
        --experiments TutorialDeadOilEgg ExampleEDPWellbore \
        --jsonl-log-dir data/eval/jsonl_logs

    # Conservative run with fewer steps
    uv run python scripts/eval/run_experiments_parallel.py --workers 2 --max-steps 50
"""

import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import subprocess


# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def get_project_root() -> Path:
    """Get project root directory."""
    script_dir = Path(__file__).parent
    return (script_dir / "../..").resolve()


async def run_experiment(
    experiment_dir: Path,
    log_dir: Path,
    semaphore: asyncio.Semaphore,
    experiment_name: str,
    model: str,
    max_steps: int,
    max_retries: int,
    retry_delay: float,
    retry_backoff: float,
    jsonl_log_dir: Path = None
) -> Tuple[str, bool, float]:
    """
    Run a single experiment and return results.

    Args:
        experiment_dir: Path to experiment directory
        log_dir: Path to logs directory (stdout/stderr)
        semaphore: Asyncio semaphore for concurrency control
        experiment_name: Name of the experiment
        model: OpenRouter model name
        max_steps: Maximum agent-tool iterations
        max_retries: Maximum API retry attempts
        retry_delay: Initial delay between retries
        retry_backoff: Exponential backoff multiplier
        jsonl_log_dir: Optional directory for JSONL conversation logs

    Returns:
        Tuple of (experiment_name, success, duration_seconds)
    """
    async with semaphore:
        instructions_file = experiment_dir / "instructions.txt"
        log_file = log_dir / f"{experiment_name}.log"

        # Check if instructions file exists
        if not instructions_file.exists():
            error_msg = f"instructions.txt not found in {experiment_dir}"
            with open(log_file, "w") as f:
                f.write(f"ERROR: {error_msg}\n")
            print(f"{Colors.FAIL}✗ {experiment_name}: {error_msg}{Colors.ENDC}")
            return (experiment_name, False, 0.0)

        # Read instructions
        instructions = instructions_file.read_text().strip()

        # Prepare command
        cmd = [
            "uv", "run", "geos-agent",
            "--instruction", instructions,
            "--workspace", str(experiment_dir),
            "--model", model,
            "--max-steps", str(max_steps),
            "--max-retries", str(max_retries),
            "--retry-delay", str(retry_delay),
            "--retry-backoff", str(retry_backoff),
        ]

        # Add JSONL log path if specified
        if jsonl_log_dir:
            jsonl_log_file = jsonl_log_dir / f"{experiment_name}.jsonl"
            cmd.extend(["--log", str(jsonl_log_file)])

        # Run experiment
        print(f"{Colors.OKCYAN}▶ Starting: {experiment_name}{Colors.ENDC}")
        start_time = asyncio.get_event_loop().time()

        try:
            with open(log_file, "w") as f:
                # Write header
                f.write(f"{'='*80}\n")
                f.write(f"Experiment: {experiment_name}\n")
                f.write(f"Started: {datetime.now().isoformat()}\n")
                f.write(f"Workspace: {experiment_dir}\n")
                f.write(f"Model: {model}\n")
                f.write(f"Max steps: {max_steps}\n")
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"{'='*80}\n\n")
                f.flush()

                # Run process
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=get_project_root()
                )

                returncode = await process.wait()

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time

            # Append footer to log
            with open(log_file, "a") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Completed: {datetime.now().isoformat()}\n")
                f.write(f"Duration: {duration:.2f}s\n")
                f.write(f"Return code: {returncode}\n")
                f.write(f"{'='*80}\n")

            if returncode == 0:
                print(f"{Colors.OKGREEN}✓ Completed: {experiment_name} ({duration:.2f}s){Colors.ENDC}")
                return (experiment_name, True, duration)
            else:
                print(f"{Colors.FAIL}✗ Failed: {experiment_name} (exit code {returncode}){Colors.ENDC}")
                return (experiment_name, False, duration)

        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time

            error_msg = f"Exception: {str(e)}"
            with open(log_file, "a") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"ERROR: {error_msg}\n")
                f.write(f"{'='*80}\n")

            print(f"{Colors.FAIL}✗ Error: {experiment_name}: {error_msg}{Colors.ENDC}")
            return (experiment_name, False, duration)


async def run_all_experiments(
    experiments_dir: Path,
    log_dir: Path,
    max_workers: int,
    model: str,
    max_steps: int,
    max_retries: int,
    retry_delay: float,
    retry_backoff: float,
    jsonl_log_dir: Path = None,
    experiment_filter: List[str] = None
):
    """
    Run all experiments concurrently with limited parallelism.

    Args:
        experiments_dir: Path to experiments directory
        log_dir: Path to logs directory (stdout/stderr)
        max_workers: Maximum number of concurrent experiments
        model: OpenRouter model name
        max_steps: Maximum agent-tool iterations
        max_retries: Maximum API retry attempts
        retry_delay: Initial delay between retries
        retry_backoff: Exponential backoff multiplier
        jsonl_log_dir: Optional directory for JSONL conversation logs
        experiment_filter: Optional list of experiment names to run
    """
    # Find all experiment directories
    experiment_dirs = [
        d for d in experiments_dir.iterdir()
        if d.is_dir() and (experiment_filter is None or d.name in experiment_filter)
    ]

    if not experiment_dirs:
        print(f"{Colors.WARNING}No experiments found in {experiments_dir}{Colors.ENDC}")
        return

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}GEOS Agent Parallel Experiment Runner{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"Experiments: {len(experiment_dirs)}")
    print(f"Max workers: {max_workers}")
    print(f"Model: {model}")
    print(f"Max steps: {max_steps}")
    print(f"Stdout/stderr logs: {log_dir}")
    if jsonl_log_dir:
        print(f"JSONL conversation logs: {jsonl_log_dir}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_workers)

    # Create tasks for all experiments
    tasks = [
        run_experiment(
            exp_dir, log_dir, semaphore, exp_dir.name,
            model, max_steps, max_retries, retry_delay, retry_backoff,
            jsonl_log_dir
        )
        for exp_dir in experiment_dirs
    ]

    # Run all experiments concurrently
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    total_duration = end_time - start_time

    # Print summary
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}Summary{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")

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
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    # Exit with error code if any failed
    if failed:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Run GEOS agent experiments in parallel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Parallelism settings
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=4,
        help="Number of concurrent workers (default: 4)"
    )

    # Directory settings
    parser.add_argument(
        "--experiments-dir",
        type=Path,
        default=None,
        help="Path to experiments directory (default: data/eval/experiments_subset)"
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=None,
        help="Path to stdout/stderr logs directory (default: data/eval/logs)"
    )
    parser.add_argument(
        "--jsonl-log-dir",
        type=Path,
        default=None,
        help="Path to JSONL conversation logs directory (default: none, no JSONL logs)"
    )

    # Experiment filtering
    parser.add_argument(
        "--experiments",
        "-e",
        nargs="+",
        help="Specific experiments to run (default: all)"
    )

    # Agent configuration (passed through to geos-agent)
    parser.add_argument(
        "--model",
        type=str,
        default="moonshotai/kimi-k2.5",
        help="OpenRouter model name (default: moonshotai/kimi-k2.5)"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=100,
        help="Maximum agent-tool iterations (default: 100)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum API retry attempts (default: 3)"
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        help="Initial delay between retries in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=2.0,
        help="Exponential backoff multiplier for retry delays (default: 2.0)"
    )

    args = parser.parse_args()

    # Set up paths
    project_root = get_project_root()
    experiments_dir = args.experiments_dir or project_root / "data/eval/experiments_subset"
    log_dir = args.log_dir or project_root / "data/eval/logs"

    # Validate experiments directory
    if not experiments_dir.exists():
        print(f"{Colors.FAIL}Error: Experiments directory not found: {experiments_dir}{Colors.ENDC}")
        sys.exit(1)

    # Create log directories
    log_dir.mkdir(parents=True, exist_ok=True)
    if args.jsonl_log_dir:
        args.jsonl_log_dir.mkdir(parents=True, exist_ok=True)

    # Run experiments
    asyncio.run(run_all_experiments(
        experiments_dir=experiments_dir,
        log_dir=log_dir,
        max_workers=args.workers,
        model=args.model,
        max_steps=args.max_steps,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        retry_backoff=args.retry_backoff,
        jsonl_log_dir=args.jsonl_log_dir,
        experiment_filter=args.experiments
    ))


if __name__ == "__main__":
    main()
