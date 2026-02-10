#!/usr/bin/env python3
"""
Batch LLM evaluation across multiple experiments.

Runs LLM judge on multiple experiment directories and aggregates results.

Usage:
    # Evaluate all experiments in a directory
    uv run python scripts/eval/batch_evaluate.py \
        --experiments-dir data/eval/experiments_subset

    # Evaluate specific experiments
    uv run python scripts/eval/batch_evaluate.py \
        --experiments-dir data/eval/experiments_subset \
        --experiments ExampleEDPWellbore TutorialDeadOilEgg

    # Custom model and output
    uv run python scripts/eval/batch_evaluate.py \
        --experiments-dir data/eval/experiments_subset \
        --model "anthropic/claude-3.5-sonnet" \
        --output data/eval/results.json

Expected directory structure:
    experiments_subset/
    ├── ExampleEDPWellbore/
    │   ├── instructions.txt
    │   ├── ground_truth/
    │   │   └── manifest.json       # Defines which files to compare
    │   └── inputs/                  # Generated files from agent
    │       └── simulation.xml
    └── TutorialDeadOilEgg/
        └── ...

manifest.json format:
    {
        "entry_point": "main.xml",          # Main XML file to compare
        "additional_files": ["base.xml"],   # Optional: other files to compare
        "ground_truth_dir": "ground_truth", # Directory with ground truth files
        "generated_dir": "inputs"           # Directory with generated files
    }
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import statistics
from datetime import datetime

# Import from other eval scripts
sys.path.insert(0, str(Path(__file__).parent))
from llm_judge_xml import load_xml, judge_xml_with_llm
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


def load_manifest(experiment_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load manifest.json from experiment directory.

    Args:
        experiment_dir: Path to experiment directory

    Returns:
        Manifest dictionary or None if not found
    """
    manifest_path = experiment_dir / "ground_truth" / "manifest.json"
    if not manifest_path.exists():
        return None

    with open(manifest_path) as f:
        return json.load(f)


def find_xml_files(experiment_dir: Path, directory: str = "inputs") -> List[Path]:
    """
    Find all XML files in a directory.

    Args:
        experiment_dir: Path to experiment directory
        directory: Subdirectory to search (e.g., "inputs", "ground_truth")

    Returns:
        List of XML file paths
    """
    xml_dir = experiment_dir / directory
    if not xml_dir.exists():
        return []

    return sorted(xml_dir.glob("**/*.xml"))


def evaluate_experiment(
    experiment_dir: Path,
    experiment_name: str,
    model: str,
    resolve_imports: bool = False,
    jsonl_log_dir: Optional[Path] = None,
    source_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate a single experiment.

    Args:
        experiment_dir: Path to experiment directory
        experiment_name: Name of the experiment
        model: OpenRouter model name
        resolve_imports: Whether to resolve XML imports
        jsonl_log_dir: Optional directory with JSONL logs for agent metrics
        source_path: Optional expected RST source path for RAG accuracy

    Returns:
        Dictionary with evaluation results
    """
    result = {
        "experiment": experiment_name,
        "status": "pending",
        "evaluations": [],
        "summary": {},
        "errors": []
    }

    # Load manifest
    manifest = load_manifest(experiment_dir)

    if manifest:
        # Use manifest to determine which files to compare
        ground_truth_dir = experiment_dir / manifest.get("ground_truth_dir", "ground_truth")
        generated_dir = experiment_dir / manifest.get("generated_dir", "inputs")

        # Get entry point file
        entry_point = manifest.get("entry_point", "main.xml")
        files_to_compare = [entry_point]

        # Add additional files if specified
        if "additional_files" in manifest:
            files_to_compare.extend(manifest["additional_files"])

    else:
        # No manifest - try to auto-detect
        ground_truth_dir = experiment_dir / "ground_truth"
        generated_dir = experiment_dir / "inputs"

        # Find all XML files in ground truth
        ground_truth_files = find_xml_files(experiment_dir, "ground_truth")

        if not ground_truth_files:
            result["status"] = "error"
            result["errors"].append("No ground truth files found and no manifest.json")
            return result

        # Use relative paths from ground_truth directory
        files_to_compare = [f.relative_to(ground_truth_dir) for f in ground_truth_files]

    # Evaluate each file
    file_scores = []

    for file_path in files_to_compare:
        ground_truth_file = ground_truth_dir / file_path
        generated_file = generated_dir / file_path

        # Check if files exist
        if not ground_truth_file.exists():
            result["errors"].append(f"Ground truth file not found: {file_path}")
            continue

        if not generated_file.exists():
            result["errors"].append(f"Generated file not found: {file_path}")
            continue

        # Load XMLs
        try:
            ground_truth_xml = load_xml(ground_truth_file, resolve_imports)
            generated_xml = load_xml(generated_file, resolve_imports)
        except Exception as e:
            result["errors"].append(f"Error loading {file_path}: {str(e)}")
            continue

        # Run LLM evaluation
        try:
            evaluation = judge_xml_with_llm(
                ground_truth_xml,
                generated_xml,
                model=model
            )

            file_eval = {
                "file": str(file_path),
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

            result["evaluations"].append(file_eval)
            file_scores.append(evaluation["overall_score"])

        except Exception as e:
            result["errors"].append(f"Error evaluating {file_path}: {str(e)}")

    # Compute summary statistics
    if file_scores:
        result["summary"] = {
            "mean_score": statistics.mean(file_scores),
            "median_score": statistics.median(file_scores),
            "min_score": min(file_scores),
            "max_score": max(file_scores),
            "num_files": len(file_scores)
        }
        result["status"] = "success"
    elif result["errors"]:
        result["status"] = "error"
    else:
        result["status"] = "no_files"
        result["errors"].append("No files evaluated")

    # Add agent metrics if JSONL log is available
    if jsonl_log_dir:
        log_file = jsonl_log_dir / f"{experiment_name}.jsonl"
        if log_file.exists():
            try:
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
    no_files = [r for r in results if r["status"] == "no_files"]

    print(f"Total experiments: {len(results)}")
    print(f"{Colors.OKGREEN}✓ Successful: {len(successful)}{Colors.ENDC}")
    print(f"{Colors.FAIL}✗ Failed: {len(failed)}{Colors.ENDC}")
    print(f"{Colors.WARNING}⊘ No files: {len(no_files)}{Colors.ENDC}")

    if successful:
        # Aggregate scores
        all_mean_scores = [r["summary"]["mean_score"] for r in successful]
        print(f"\n{Colors.BOLD}Score Statistics:{Colors.ENDC}")
        print(f"  Mean:   {statistics.mean(all_mean_scores):.2f}/10")
        print(f"  Median: {statistics.median(all_mean_scores):.2f}/10")
        print(f"  Range:  {min(all_mean_scores):.2f} - {max(all_mean_scores):.2f}")

        # Per-experiment scores
        print(f"\n{Colors.BOLD}Individual Experiment Scores:{Colors.ENDC}")
        for result in sorted(successful, key=lambda r: r["summary"]["mean_score"], reverse=True):
            score = result["summary"]["mean_score"]
            name = result["experiment"]
            num_files = result["summary"]["num_files"]

            # Color code based on score
            if score >= 8.0:
                color = Colors.OKGREEN
            elif score >= 6.0:
                color = Colors.OKCYAN
            elif score >= 4.0:
                color = Colors.WARNING
            else:
                color = Colors.FAIL

            print(f"  {color}{score:5.2f}/10{Colors.ENDC}  {name} ({num_files} file{'s' if num_files != 1 else ''})")

    # Failed experiments
    if failed:
        print(f"\n{Colors.FAIL}Failed Experiments:{Colors.ENDC}")
        for result in failed:
            print(f"  ✗ {result['experiment']}")
            for error in result["errors"][:3]:  # Show first 3 errors
                print(f"    - {error}")

    # Aggregate agent metrics if available
    results_with_metrics = [r for r in successful if "agent_metrics" in r]
    if results_with_metrics:
        print(f"\n{Colors.BOLD}Agent Execution Metrics:{Colors.ENDC}")

        # Aggregate tool errors
        total_calls = sum(r["agent_metrics"]["tool_errors"]["total_tool_calls"] for r in results_with_metrics)
        total_errors = sum(r["agent_metrics"]["tool_errors"]["total_errors"] for r in results_with_metrics)
        avg_error_rate = total_errors / total_calls if total_calls > 0 else 0.0

        print(f"  Total tool calls: {total_calls}")
        print(f"  Total errors: {total_errors}")
        print(f"  Avg error rate: {avg_error_rate:.1%}")

        # Aggregate RAG metrics if available
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
        help="Path to experiments directory"
    )

    # Agent metrics options
    parser.add_argument(
        "--jsonl-log-dir",
        type=Path,
        help="Path to JSONL log directory for agent metrics (optional)"
    )
    parser.add_argument(
        "--source-path",
        type=str,
        help="Expected RST source path for RAG accuracy (optional)"
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
        "--resolve-imports",
        "-r",
        action="store_true",
        help="Resolve XML imports before comparison"
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
        help="Print detailed per-file evaluations"
    )

    args = parser.parse_args()

    # Validate experiments directory
    if not args.experiments_dir.exists():
        print(f"{Colors.FAIL}Error: Experiments directory not found: {args.experiments_dir}{Colors.ENDC}")
        sys.exit(1)

    # Find experiments
    experiment_dirs = [
        d for d in args.experiments_dir.iterdir()
        if d.is_dir() and (args.experiments is None or d.name in args.experiments)
    ]

    if not experiment_dirs:
        print(f"{Colors.WARNING}No experiments found in {args.experiments_dir}{Colors.ENDC}")
        sys.exit(1)

    print(f"{Colors.BOLD}Evaluating {len(experiment_dirs)} experiments...{Colors.ENDC}")
    print(f"Model: {args.model}\n")

    # Evaluate each experiment
    results = []
    for i, exp_dir in enumerate(experiment_dirs, 1):
        exp_name = exp_dir.name
        print(f"{Colors.OKCYAN}[{i}/{len(experiment_dirs)}] Evaluating: {exp_name}{Colors.ENDC}")

        result = evaluate_experiment(
            exp_dir,
            exp_name,
            args.model,
            args.resolve_imports,
            args.jsonl_log_dir,
            args.source_path
        )

        results.append(result)

        # Print brief status
        if result["status"] == "success":
            score = result["summary"]["mean_score"]
            print(f"  {Colors.OKGREEN}✓ Score: {score:.2f}/10{Colors.ENDC}")

            # Print agent metrics if available
            if "agent_metrics" in result:
                metrics = result["agent_metrics"]
                error_rate = metrics["tool_errors"]["error_rate"]
                print(f"    Tool error rate: {error_rate:.1%}")

                if "rag_retrieval" in metrics:
                    rag_rate = metrics["rag_retrieval"]["relevant_chunk_rate"]
                    print(f"    RAG accuracy: {rag_rate:.1%}")

        elif result["status"] == "error":
            print(f"  {Colors.FAIL}✗ Failed: {result['errors'][0] if result['errors'] else 'Unknown error'}{Colors.ENDC}")
        else:
            print(f"  {Colors.WARNING}⊘ No files to evaluate{Colors.ENDC}")

        # Print detailed per-file results if verbose
        if args.verbose and result["status"] == "success":
            for file_eval in result["evaluations"]:
                print(f"    - {file_eval['file']}: {file_eval['scores']['overall']:.2f}/10")

    # Print summary
    print_summary_report(results)

    # Save results if requested
    if args.output:
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "model": args.model,
            "resolve_imports": args.resolve_imports,
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
