#!/usr/bin/env python3
"""
Batch reference-based XML evaluation for all GEOS agent experiments.

Uses lxml_xml_eval.py (no LLM required) to score agent-generated XML files
against ground truth across all experiments in one run.

Usage:
    # Evaluate all 46 experiments (default paths)
    uv run python scripts/eval/batch_lxml_evaluate.py

    # Custom directories
    uv run python scripts/eval/batch_lxml_evaluate.py \\
        --experiments-dir data/eval/experiments_subset \\
        --ground-truth-dir data/eval/experiments_gt \\
        --results-dir data/eval/eval_v2_results

    # Evaluate specific experiments only
    uv run python scripts/eval/batch_lxml_evaluate.py \\
        --experiments ExampleEDPWellbore TutorialDeadOilEgg

    # Skip saving individual JSONs (summary only)
    uv run python scripts/eval/batch_lxml_evaluate.py --no-save

Expected directory structure:
    experiments/                  # Agent-generated outputs
    ├── ExampleEDPWellbore/
    │   └── inputs/               # Agent-generated XML files
    └── TutorialDeadOilEgg/
        └── inputs/

    experiments_gt/               # Ground truth
    ├── ExampleEDPWellbore/
    │   └── inputs/               # Reference XML files
    └── TutorialDeadOilEgg/
        └── inputs/

    eval_v2_results/              # Output: per-experiment <name>_lxml.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def get_project_root() -> Path:
    return (Path(__file__).parent / "../..").resolve()


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

class C:
    HEADER  = "\033[95m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    WARNING = "\033[93m"
    FAIL    = "\033[91m"
    ENDC    = "\033[0m"
    BOLD    = "\033[1m"


# ---------------------------------------------------------------------------
# Single-experiment evaluation
# ---------------------------------------------------------------------------

def evaluate_one(
    experiment_name: str,
    experiments_dir: Path,
    gt_dir: Path,
    results_dir: Path | None,
    save: bool,
) -> dict:
    """
    Run lxml evaluation for one experiment. Returns a result dict.

    The result dict always contains:
      "experiment", "status", "error" (if failed),
      and all keys from lxml_xml_eval.evaluate_directories() if successful.
    """
    # Import here so the module path insert in main() takes effect first.
    from lxml_xml_eval import evaluate_directories

    gen_inputs = experiments_dir / experiment_name / "inputs"
    gt_inputs  = gt_dir / experiment_name / "inputs"

    result: dict = {"experiment": experiment_name}

    if not gt_inputs.exists():
        result["status"] = "error"
        result["error"]  = f"Ground-truth inputs not found: {gt_inputs}"
        return result

    if not gen_inputs.exists():
        result["status"] = "error"
        result["error"]  = f"Generated inputs not found: {gen_inputs}"
        return result

    try:
        eval_result = evaluate_directories(gt_inputs, gen_inputs)
        result.update(eval_result)
        result["status"] = "success"
    except FileNotFoundError as exc:
        result["status"] = "error"
        result["error"]  = str(exc)
        return result
    except Exception as exc:  # noqa: BLE001
        result["status"] = "error"
        result["error"]  = f"{type(exc).__name__}: {exc}"
        return result

    if save and results_dir is not None:
        results_dir.mkdir(parents=True, exist_ok=True)
        out_path = results_dir / f"{experiment_name}_lxml.json"
        out_path.write_text(json.dumps(result, indent=2))

    return result


# ---------------------------------------------------------------------------
# Summary printing
# ---------------------------------------------------------------------------

def print_summary(results: list[dict]) -> None:
    successful = [r for r in results if r["status"] == "success"]
    failed     = [r for r in results if r["status"] != "success"]

    W = 80
    print(f"\n{C.BOLD}{C.HEADER}{'=' * W}{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}  BATCH LXML EVALUATION SUMMARY{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}{'=' * W}{C.ENDC}")
    print(f"  Total experiments : {len(results)}")
    print(f"  {C.GREEN}Successful        : {len(successful)}{C.ENDC}")
    if failed:
        print(f"  {C.FAIL}Failed            : {len(failed)}{C.ENDC}")

    if successful:
        scores = [r["overall_score"] for r in successful]
        print(f"\n  {C.BOLD}Score statistics (0–10):{C.ENDC}")
        print(f"    Mean   : {statistics.mean(scores):.2f}")
        print(f"    Median : {statistics.median(scores):.2f}")
        print(f"    Std    : {statistics.stdev(scores):.2f}" if len(scores) > 1 else "")
        print(f"    Range  : {min(scores):.2f} – {max(scores):.2f}")
        pass_count = sum(1 for s in scores if s >= 7.0)
        print(f"    Pass ≥7: {pass_count}/{len(scores)}")

        print(f"\n  {C.BOLD}Per-experiment scores (sorted):{C.ENDC}")
        for r in sorted(successful, key=lambda x: x["overall_score"], reverse=True):
            s    = r["overall_score"]
            name = r["experiment"]
            color = C.GREEN if s >= 7.0 else (C.WARNING if s >= 4.0 else C.FAIL)
            # Dimension scores as a compact string
            dims = r.get("dimension_scores", {})
            dim_str = "  ".join(
                f"{k[:4]}={v:.2f}"
                for k, v in dims.items()
            )
            print(f"  {color}{s:5.2f}{C.ENDC}  {name:<55}  {dim_str}")

    if failed:
        print(f"\n  {C.FAIL}Failed experiments:{C.ENDC}")
        for r in failed:
            print(f"    {r['experiment']}: {r.get('error', 'unknown error')}")

    print(f"\n{C.BOLD}{C.HEADER}{'=' * W}{C.ENDC}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    project_root = get_project_root()

    parser = argparse.ArgumentParser(
        description="Batch lxml-based XML evaluation for all GEOS agent experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--experiments-dir", "-d",
        type=Path,
        default=project_root / "data/eval/experiments",
        help="Directory of agent-generated experiment outputs "
             "(default: data/eval/experiments)",
    )
    parser.add_argument(
        "--ground-truth-dir", "-g",
        type=Path,
        default=project_root / "data/eval/experiments_gt",
        help="Directory of ground-truth experiments "
             "(default: data/eval/experiments_gt)",
    )
    parser.add_argument(
        "--results-dir", "-r",
        type=Path,
        default=project_root / "data/eval/eval_v2_results",
        help="Directory to write per-experiment *_lxml.json files "
             "(default: data/eval/eval_v2_results)",
    )
    parser.add_argument(
        "--experiments", "-e",
        nargs="+",
        metavar="NAME",
        help="Specific experiment names to evaluate (default: all)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write per-experiment JSON result files",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Write aggregated results JSON to this file (optional)",
    )
    parser.add_argument(
        "--rtol",
        type=float,
        default=None,
        help="Override numeric comparison tolerance passed to lxml evaluator",
    )

    args = parser.parse_args()

    # Make lxml_xml_eval importable regardless of cwd.
    sys.path.insert(0, str(Path(__file__).parent))

    # If rtol override requested, monkey-patch the module constant.
    if args.rtol is not None:
        import lxml_xml_eval as _m
        _m.NUMERIC_RTOL = args.rtol

    # Validate directories.
    if not args.experiments_dir.exists():
        print(f"{C.FAIL}Error: experiments directory not found: {args.experiments_dir}{C.ENDC}")
        sys.exit(1)
    if not args.ground_truth_dir.exists():
        print(f"{C.FAIL}Error: ground-truth directory not found: {args.ground_truth_dir}{C.ENDC}")
        sys.exit(1)

    # Discover experiments.
    all_dirs = sorted(
        d for d in args.experiments_dir.iterdir() if d.is_dir()
    )
    if args.experiments:
        experiment_names = [
            d.name for d in all_dirs if d.name in args.experiments
        ]
        missing = set(args.experiments) - set(experiment_names)
        if missing:
            print(f"{C.WARNING}Warning: experiments not found in {args.experiments_dir}: "
                  f"{', '.join(sorted(missing))}{C.ENDC}")
    else:
        experiment_names = [d.name for d in all_dirs]

    if not experiment_names:
        print(f"{C.WARNING}No experiments found.{C.ENDC}")
        sys.exit(1)

    save = not args.no_save

    print(f"\n{C.BOLD}{C.HEADER}{'=' * 80}{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}  GEOS Agent Batch lxml Evaluation{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}{'=' * 80}{C.ENDC}")
    print(f"  Experiments dir : {args.experiments_dir}")
    print(f"  Ground-truth dir: {args.ground_truth_dir}")
    print(f"  Results dir     : {args.results_dir if save else '(not saving)'}")
    print(f"  Experiments     : {len(experiment_names)}")
    print(f"{C.BOLD}{C.HEADER}{'=' * 80}{C.ENDC}\n")

    results: list[dict] = []
    for i, name in enumerate(experiment_names, 1):
        print(f"{C.CYAN}[{i:3d}/{len(experiment_names)}] {name}{C.ENDC}", end="  ", flush=True)
        result = evaluate_one(name, args.experiments_dir, args.ground_truth_dir, args.results_dir, save)
        results.append(result)

        if result["status"] == "success":
            s = result["overall_score"]
            color = C.GREEN if s >= 7.0 else (C.WARNING if s >= 4.0 else C.FAIL)
            print(f"{color}{s:.2f}/10{C.ENDC}")
        else:
            print(f"{C.FAIL}FAILED: {result.get('error', '')}{C.ENDC}")

    # Summary report.
    print_summary(results)

    # Optional aggregated output JSON.
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now().isoformat(),
            "experiments_dir": str(args.experiments_dir),
            "ground_truth_dir": str(args.ground_truth_dir),
            "total": len(results),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "results": results,
        }
        args.output.write_text(json.dumps(payload, indent=2))
        print(f"Aggregated results saved to: {args.output}")


if __name__ == "__main__":
    main()
