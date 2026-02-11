#!/usr/bin/env python3
"""
Batch LLM evaluation across multiple experiments.

Runs LLM judge on multiple experiment directories and aggregates results.
Uses multi-file bundle comparison: all XML files from the agent's output
directory are compared as a whole against all XML files from the ground
truth directory.

Usage:
    # XML quality only
    uv run python scripts/eval/batch_evaluate.py \
        --experiments-dir data/eval/experiments_subset \
        --ground-truth-dir data/eval/experiments_gt

    # All 3 eval dimensions (XML quality + tool errors + RAG accuracy)
    uv run python scripts/eval/batch_evaluate.py \
        --experiments-dir data/eval/experiments_subset \
        --ground-truth-dir data/eval/experiments_gt \
        --jsonl-log-dir data/eval/jsonl_logs

    # Evaluate specific experiments
    uv run python scripts/eval/batch_evaluate.py \
        --experiments-dir data/eval/experiments_subset \
        --ground-truth-dir data/eval/experiments_gt \
        --jsonl-log-dir data/eval/jsonl_logs \
        --experiments ExampleEDPWellbore TutorialDeadOilEgg

Expected directory structure:
    experiments_subset/             # Agent output experiments
    ├── ExampleEDPWellbore/
    │   ├── instructions.txt
    │   └── inputs/                 # Agent-generated XML files
    │       ├── main.xml
    │       └── base.xml
    └── TutorialDeadOilEgg/
        └── ...

    experiments_gt/                 # Ground truth (separate directory)
    ├── ExampleEDPWellbore/
    │   └── inputs/                 # Ground truth XML files
    │       ├── WellboreBase.xml
    │       └── WellboreBenchmark.xml
    └── TutorialDeadOilEgg/
        └── ...
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import statistics
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import from other eval scripts
sys.path.insert(0, str(Path(__file__).parent))
from llm_judge_xml import collect_xml_bundle, judge_xml_bundle_with_llm
from compute_agent_metrics import analyze_log


class Colors:
    """Terminal colors for output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def load_experiment_metadata(experiment_dir: Path) -> Dict[str, Any]:
    """
    Load metadata.json from an experiment directory.

    Returns:
        Metadata dictionary, or empty dict if not found.
    """
    metadata_path = experiment_dir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            return json.load(f)
    return {}


def evaluate_experiment(
    experiment_dir: Path,
    experiment_name: str,
    model: str,
    ground_truth_base_dir: Optional[Path] = None,
    jsonl_log_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Evaluate a single experiment using multi-file bundle comparison.

    Collects all XML files from the ground truth and generated directories,
    bundles them with file path labels, and sends the bundles to the LLM
    judge for a single holistic evaluation.

    If a JSONL log is available, also computes tool error metrics and
    RAG retrieval accuracy (using rst_path from metadata.json).

    Args:
        experiment_dir: Path to experiment directory (agent output)
        experiment_name: Name of the experiment
        model: OpenRouter model name
        ground_truth_base_dir: Base directory containing ground truth experiments
                               (GT is at ground_truth_base_dir/<experiment_name>/inputs/)
        jsonl_log_dir: Optional directory with JSONL logs for agent metrics

    Returns:
        Dictionary with evaluation results
    """
    result = {
        "experiment": experiment_name,
        "status": "pending",
        "evaluation": {},
        "errors": [],
        "gt_xml_count": 0,
        "gen_xml_count": 0,
    }

    # Determine ground truth directory
    if ground_truth_base_dir:
        gt_dir = ground_truth_base_dir / experiment_name / "inputs"
    else:
        # Fallback: look inside the experiment dir itself
        gt_dir = experiment_dir / "ground_truth"

    # Generated files are in the experiment's inputs/ directory
    gen_dir = experiment_dir / "inputs"

    # Validate directories exist
    if not gt_dir.exists():
        result["status"] = "error"
        result["errors"].append(f"Ground truth directory not found: {gt_dir}")
        return result

    if not gen_dir.exists():
        result["status"] = "error"
        result["errors"].append(f"Generated directory not found: {gen_dir}")
        return result

    # Collect XML bundles
    try:
        gt_bundle = collect_xml_bundle(gt_dir)
        gt_count = len(list(gt_dir.rglob("*.xml")))
        result["gt_xml_count"] = gt_count
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Error collecting ground truth XMLs: {str(e)}")
        return result

    try:
        gen_bundle = collect_xml_bundle(gen_dir)
        gen_count = len(list(gen_dir.rglob("*.xml")))
        result["gen_xml_count"] = gen_count
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Error collecting generated XMLs: {str(e)}")
        return result

    if not gt_bundle:
        result["status"] = "error"
        result["errors"].append(f"No XML files found in ground truth: {gt_dir}")
        return result

    if not gen_bundle:
        result["status"] = "error"
        result["errors"].append(f"No XML files found in generated: {gen_dir}")
        return result

    # Run LLM bundle evaluation
    try:
        evaluation = judge_xml_bundle_with_llm(
            gt_bundle,
            gen_bundle,
            model=model
        )

        result["evaluation"] = {
            "scores": {
                "overall": evaluation["overall_score"],
                "structural_correctness": evaluation["structural_correctness"],
                "parameter_accuracy": evaluation["parameter_accuracy"],
                "completeness": evaluation["completeness"],
                "semantic_equivalence": evaluation["semantic_equivalence"]
            },
            "explanation": evaluation["explanation"],
            "critical_errors": evaluation.get("critical_errors", []),
            "minor_issues": evaluation.get("minor_issues", []),
            "strengths": evaluation.get("strengths", [])
        }
        result["status"] = "success"

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Error during LLM evaluation: {str(e)}")

    # Add agent metrics if JSONL log is available
    if jsonl_log_dir:
        log_file = jsonl_log_dir / f"{experiment_name}.jsonl"
        if log_file.exists():
            try:
                # Read per-experiment rst_path from metadata.json for RAG accuracy
                metadata = load_experiment_metadata(experiment_dir)
                source_path = metadata.get("rst_path") or None
                agent_metrics = analyze_log(log_file, source_path)
                result["agent_metrics"] = agent_metrics
            except Exception as e:
                result["errors"].append(f"Error analyzing agent metrics: {str(e)}")

    return result


def print_summary_report(results: List[Dict[str, Any]]):
    """
    Print a summary report of all evaluations.

    Args:
        results: List of evaluation results
    """
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}BATCH EVALUATION SUMMARY{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    # Overall statistics
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]

    print(f"Total experiments: {len(results)}")
    print(f"{Colors.OKGREEN}Successful: {len(successful)}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {len(failed)}{Colors.ENDC}")

    if successful:
        # Aggregate scores
        all_scores = [r["evaluation"]["scores"]["overall"] for r in successful]
        print(f"\n{Colors.BOLD}Score Statistics:{Colors.ENDC}")
        print(f"  Mean:   {statistics.mean(all_scores):.2f}/10")
        print(f"  Median: {statistics.median(all_scores):.2f}/10")
        print(f"  Range:  {min(all_scores):.2f} - {max(all_scores):.2f}")

        # Per-experiment scores
        print(f"\n{Colors.BOLD}Individual Experiment Scores:{Colors.ENDC}")
        for result in sorted(successful, key=lambda r: r["evaluation"]["scores"]["overall"], reverse=True):
            score = result["evaluation"]["scores"]["overall"]
            name = result["experiment"]
            gt_count = result["gt_xml_count"]
            gen_count = result["gen_xml_count"]

            # Color code based on score
            if score >= 8.0:
                color = Colors.OKGREEN
            elif score >= 6.0:
                color = Colors.OKCYAN
            elif score >= 4.0:
                color = Colors.WARNING
            else:
                color = Colors.FAIL

            print(f"  {color}{score:5.2f}/10{Colors.ENDC}  {name} (GT: {gt_count} xml, Gen: {gen_count} xml)")

    # Failed experiments
    if failed:
        print(f"\n{Colors.FAIL}Failed Experiments:{Colors.ENDC}")
        for result in failed:
            print(f"  {result['experiment']}")
            for error in result["errors"][:3]:
                print(f"    - {error}")

    # Aggregate agent metrics if available
    results_with_metrics = [r for r in successful if "agent_metrics" in r]
    if results_with_metrics:
        print(f"\n{Colors.BOLD}Agent Execution Metrics:{Colors.ENDC}")

        total_calls = sum(r["agent_metrics"]["tool_errors"]["total_tool_calls"] for r in results_with_metrics)
        total_errors = sum(r["agent_metrics"]["tool_errors"]["total_errors"] for r in results_with_metrics)
        avg_error_rate = total_errors / total_calls if total_calls > 0 else 0.0

        print(f"  Total tool calls: {total_calls}")
        print(f"  Total errors: {total_errors}")
        print(f"  Avg error rate: {avg_error_rate:.1%}")

        results_with_rag = [r for r in results_with_metrics if "rag_retrieval" in r["agent_metrics"]]
        if results_with_rag:
            total_chunks = sum(r["agent_metrics"]["rag_retrieval"]["total_chunks_retrieved"] for r in results_with_rag)
            relevant_chunks = sum(r["agent_metrics"]["rag_retrieval"]["relevant_chunks"] for r in results_with_rag)
            avg_rag_rate = relevant_chunks / total_chunks if total_chunks > 0 else 0.0

            print(f"\n  RAG Retrieval:")
            print(f"    Total chunks: {total_chunks}")
            print(f"    Relevant chunks: {relevant_chunks}")
            print(f"    Avg relevance: {avg_rag_rate:.1%}")

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Batch LLM evaluation for GEOS agent experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Required arguments
    parser.add_argument(
        "--experiments-dir",
        "-d",
        type=Path,
        required=True,
        help="Path to experiments directory (agent output)"
    )
    parser.add_argument(
        "--ground-truth-dir",
        "-g",
        type=Path,
        required=True,
        help="Path to ground truth base directory (e.g., data/eval/experiments_gt). "
             "Each experiment's GT is at <ground-truth-dir>/<experiment_name>/inputs/"
    )

    # Agent metrics options
    parser.add_argument(
        "--jsonl-log-dir",
        type=Path,
        help="Path to JSONL log directory for agent metrics (optional). "
             "RAG accuracy uses rst_path from each experiment's metadata.json."
    )

    # Optional arguments
    parser.add_argument(
        "--experiments",
        "-e",
        nargs="+",
        help="Specific experiments to evaluate (default: all)"
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="anthropic/claude-3.5-sonnet",
        help="OpenRouter model name (default: anthropic/claude-3.5-sonnet)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Path to save results JSON (optional)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed evaluation explanations"
    )

    args = parser.parse_args()

    # Validate directories
    if not args.experiments_dir.exists():
        print(f"{Colors.FAIL}Error: Experiments directory not found: {args.experiments_dir}{Colors.ENDC}")
        sys.exit(1)

    if not args.ground_truth_dir.exists():
        print(f"{Colors.FAIL}Error: Ground truth directory not found: {args.ground_truth_dir}{Colors.ENDC}")
        sys.exit(1)

    # Find experiments
    experiment_dirs = sorted([
        d for d in args.experiments_dir.iterdir()
        if d.is_dir() and (args.experiments is None or d.name in args.experiments)
    ])

    if not experiment_dirs:
        print(f"{Colors.WARNING}No experiments found in {args.experiments_dir}{Colors.ENDC}")
        sys.exit(1)

    print(f"{Colors.BOLD}Evaluating {len(experiment_dirs)} experiments...{Colors.ENDC}")
    print(f"Model: {args.model}")
    print(f"Ground truth: {args.ground_truth_dir}\n")

    # Evaluate each experiment
    results = []
    for i, exp_dir in enumerate(experiment_dirs, 1):
        exp_name = exp_dir.name
        print(f"{Colors.OKCYAN}[{i}/{len(experiment_dirs)}] Evaluating: {exp_name}{Colors.ENDC}")

        result = evaluate_experiment(
            exp_dir,
            exp_name,
            args.model,
            ground_truth_base_dir=args.ground_truth_dir,
            jsonl_log_dir=args.jsonl_log_dir,
        )

        results.append(result)

        # Print brief status
        if result["status"] == "success":
            score = result["evaluation"]["scores"]["overall"]
            gt_n = result["gt_xml_count"]
            gen_n = result["gen_xml_count"]
            print(f"  {Colors.OKGREEN}Score: {score:.2f}/10  (GT: {gt_n} xml, Gen: {gen_n} xml){Colors.ENDC}")

            # Print agent metrics if available
            if "agent_metrics" in result:
                metrics = result["agent_metrics"]
                error_rate = metrics["tool_errors"]["error_rate"]
                print(f"    Tool error rate: {error_rate:.1%}")

                if "rag_retrieval" in metrics:
                    rag_rate = metrics["rag_retrieval"]["relevant_chunk_rate"]
                    print(f"    RAG accuracy: {rag_rate:.1%}")

            # Print detailed explanation if verbose
            if args.verbose:
                explanation = result["evaluation"].get("explanation", "")
                if explanation:
                    print(f"    Explanation: {explanation[:200]}...")

        elif result["status"] == "error":
            print(f"  {Colors.FAIL}Failed: {result['errors'][0] if result['errors'] else 'Unknown error'}{Colors.ENDC}")

    # Print summary
    print_summary_report(results)

    # Save results if requested
    if args.output:
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "model": args.model,
            "ground_truth_dir": str(args.ground_truth_dir),
            "total_experiments": len(results),
            "results": results
        }

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"Results saved to: {args.output}")

    # Exit with error if any evaluations failed
    if any(r["status"] == "error" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
