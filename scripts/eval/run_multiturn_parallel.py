#!/usr/bin/env python3
"""
Run multi-turn evaluation experiments concurrently.

Each experiment gets its own process for full isolation (separate ChromaDB
connections, OpenAI clients, etc.). Results and logs are written to the
log directory.

Usage:
    # Run all experiments in the subset with 2 workers
    uv run python scripts/eval/run_multiturn_parallel.py \
        --experiments-dir data/eval/experiments_subset \
        --workers 2

    # Run specific experiments with custom models
    uv run python scripts/eval/run_multiturn_parallel.py \
        --experiments TutorialDeadOilEgg ExampleEDPWellbore \
        --agent-model "moonshotai/kimi-k2.5" \
        --simulator-model "anthropic/claude-sonnet-4" \
        --workers 4

    # Full run with custom log directory
    uv run python scripts/eval/run_multiturn_parallel.py \
        --experiments-dir data/eval/experiments \
        --log-dir data/eval/multiturn_logs \
        --workers 8
"""

import argparse
import asyncio
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Colors for terminal output
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
    return (Path(__file__).parent / "../..").resolve()


def run_single_experiment(
    experiment_dir: str,
    log_dir: str,
    agent_model: str,
    simulator_model: str,
    max_agent_steps: int,
    max_total_turns: int,
    max_simulator_turns: int,
    eval_preamble: Optional[str],
) -> Tuple[str, bool, float, int, int, Optional[str]]:
    """Run a single experiment in a separate process.

    This function is the target for ProcessPoolExecutor. It imports
    everything locally to ensure full process isolation.

    Returns:
        (experiment_name, success, duration, user_turns, agent_questions, error)
    """
    # Lazy imports — each process gets a clean import
    import os
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))

    from dotenv import load_dotenv
    load_dotenv()

    from run_multiturn_experiment import MultiTurnConfig, MultiTurnExperimentRunner

    experiment_path = Path(experiment_dir)
    experiment_name = experiment_path.name
    log_path = Path(log_dir)

    config = MultiTurnConfig(
        agent_model=agent_model,
        simulator_model=simulator_model,
        max_agent_steps=max_agent_steps,
        max_total_turns=max_total_turns,
        max_simulator_turns=max_simulator_turns,
        eval_preamble=eval_preamble,
    )

    try:
        runner = MultiTurnExperimentRunner(experiment_path, config)
        result = runner.run()

        # Save multi-turn log
        multiturn_log_file = log_path / f"{experiment_name}_multiturn.json"
        with open(multiturn_log_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Save standard conversation log (batch_evaluate.py compatible)
        jsonl_log_file = log_path / f"{experiment_name}.jsonl"
        with open(jsonl_log_file, "w", encoding="utf-8") as f:
            json.dump(result["conversation_log"], f, indent=2, ensure_ascii=False)

        return (
            experiment_name,
            not result.get("agent_terminated", False),
            result["total_duration_seconds"],
            result["total_user_turns"],
            result["total_agent_questions"],
            None,
        )

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        # Write error log
        error_log = log_path / f"{experiment_name}_error.log"
        with open(error_log, "w") as f:
            import traceback
            f.write(f"Experiment: {experiment_name}\n")
            f.write(f"Error: {error_msg}\n\n")
            traceback.print_exc(file=f)

        return (experiment_name, False, 0.0, 0, 0, error_msg)


async def run_all_experiments(
    experiments_dir: Path,
    log_dir: Path,
    max_workers: int,
    agent_model: str,
    simulator_model: str,
    max_agent_steps: int,
    max_total_turns: int,
    max_simulator_turns: int,
    experiment_filter: Optional[List[str]] = None,
    eval_preamble: Optional[str] = None,
):
    """Run all experiments using ProcessPoolExecutor for isolation."""

    # Find experiment directories
    experiment_dirs = sorted([
        d for d in experiments_dir.iterdir()
        if d.is_dir()
        and (d / "instructions.txt").exists()
        and (experiment_filter is None or d.name in experiment_filter)
    ])

    if not experiment_dirs:
        print(f"{Colors.WARNING}No experiments found in {experiments_dir}{Colors.ENDC}")
        return

    # Print header
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}GEOS Agent Multi-Turn Parallel Experiment Runner{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"Experiments:      {len(experiment_dirs)}")
    print(f"Max workers:      {max_workers}")
    print(f"Agent model:      {agent_model}")
    print(f"Simulator model:  {simulator_model}")
    print(f"Max agent steps:  {max_agent_steps}")
    print(f"Max total turns:  {max_total_turns}")
    print(f"Log directory:    {log_dir}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")

    log_dir.mkdir(parents=True, exist_ok=True)

    # Run experiments in parallel processes
    loop = asyncio.get_event_loop()
    start_time = loop.time()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            loop.run_in_executor(
                executor,
                run_single_experiment,
                str(exp_dir),
                str(log_dir),
                agent_model,
                simulator_model,
                max_agent_steps,
                max_total_turns,
                max_simulator_turns,
                eval_preamble,
            )
            for exp_dir in experiment_dirs
        ]
        results = await asyncio.gather(*futures)

    total_time = loop.time() - start_time

    # Print summary
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}Summary{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")

    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    print(f"Total experiments:  {len(results)}")
    print(f"{Colors.OKGREEN}Successful:         {len(successful)}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed:             {len(failed)}{Colors.ENDC}")
    print(f"Total wall time:    {total_time:.1f}s")

    if successful:
        avg_duration = sum(r[2] for r in successful) / len(successful)
        avg_turns = sum(r[3] for r in successful) / len(successful)
        avg_questions = sum(r[4] for r in successful) / len(successful)
        print(f"\n  Avg duration (successful):     {avg_duration:.1f}s")
        print(f"  Avg user turns (successful):   {avg_turns:.1f}")
        print(f"  Avg agent questions:           {avg_questions:.1f}")

    # Per-experiment detail
    print(f"\n{Colors.BOLD}Per-experiment results:{Colors.ENDC}")
    for name, success, duration, user_turns, agent_questions, error in results:
        if success:
            print(
                f"  {Colors.OKGREEN}✓ {name}{Colors.ENDC}  "
                f"({duration:.1f}s, {user_turns} turns, {agent_questions} questions)"
            )
        else:
            error_preview = (error[:60] + "...") if error and len(error) > 60 else error
            print(
                f"  {Colors.FAIL}✗ {name}{Colors.ENDC}  "
                f"({duration:.1f}s) — {error_preview or 'unknown error'}"
            )

    print(f"\n{Colors.OKBLUE}Logs saved to: {log_dir}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")

    if failed:
        sys.exit(1)


def main():
    from run_multiturn_experiment import DEFAULT_EVAL_PREAMBLE

    parser = argparse.ArgumentParser(
        description="Run multi-turn GEOS agent experiments in parallel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Parallelism
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=2,
        help="Number of concurrent workers (default: 2)",
    )

    # Directories
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
        help="Path to log output directory (default: data/eval/multiturn_logs)",
    )

    # Experiment filtering
    parser.add_argument(
        "--experiments", "-e",
        nargs="+",
        help="Specific experiments to run (default: all)",
    )

    # Model configuration
    parser.add_argument(
        "--agent-model",
        type=str,
        default="moonshotai/kimi-k2.5",
        help="OpenRouter model for the GEOS agent (default: moonshotai/kimi-k2.5)",
    )
    parser.add_argument(
        "--simulator-model",
        type=str,
        default="anthropic/claude-sonnet-4",
        help="OpenRouter model for the user simulator (default: anthropic/claude-sonnet-4)",
    )

    # Agent/simulator limits
    parser.add_argument(
        "--max-agent-steps",
        type=int,
        default=100,
        help="Max tool-call iterations per agent step() (default: 100)",
    )
    parser.add_argument(
        "--max-total-turns",
        type=int,
        default=15,
        help="Max user turns (initial + follow-ups) (default: 15)",
    )
    parser.add_argument(
        "--max-simulator-turns",
        type=int,
        default=10,
        help="Max turns the simulator will produce (default: 10)",
    )

    # Eval isolation
    parser.add_argument(
        "--no-eval-preamble",
        action="store_true",
        help="Disable the default eval preamble",
    )

    args = parser.parse_args()

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    # Resolve paths
    project_root = get_project_root()
    experiments_dir = args.experiments_dir or project_root / "data/eval/experiments_subset"
    log_dir = args.log_dir or project_root / "data/eval/multiturn_logs"

    if not experiments_dir.exists():
        print(f"{Colors.FAIL}Error: Experiments directory not found: {experiments_dir}{Colors.ENDC}")
        sys.exit(1)

    # Resolve eval preamble
    eval_preamble = None if args.no_eval_preamble else DEFAULT_EVAL_PREAMBLE

    asyncio.run(run_all_experiments(
        experiments_dir=experiments_dir,
        log_dir=log_dir,
        max_workers=args.workers,
        agent_model=args.agent_model,
        simulator_model=args.simulator_model,
        max_agent_steps=args.max_agent_steps,
        max_total_turns=args.max_total_turns,
        max_simulator_turns=args.max_simulator_turns,
        experiment_filter=args.experiments,
        eval_preamble=eval_preamble,
    ))


if __name__ == "__main__":
    main()
