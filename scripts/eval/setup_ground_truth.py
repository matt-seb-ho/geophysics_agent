#!/usr/bin/env python3
"""
Helper script to set up ground truth directories for experiments.

Creates the directory structure and manifest.json for each experiment.

Usage:
    # Set up ground truth for a single experiment
    uv run python scripts/eval/setup_ground_truth.py \
        --experiment data/eval/experiments_subset/ExampleEDPWellbore \
        --entry-point main.xml

    # Set up with additional files (imports)
    uv run python scripts/eval/setup_ground_truth.py \
        --experiment data/eval/experiments_subset/TutorialHydraulic \
        --entry-point case.xml \
        --additional base.xml tables/data.csv

    # Batch setup for all experiments
    uv run python scripts/eval/setup_ground_truth.py \
        --experiments-dir data/eval/experiments_subset \
        --auto-detect

After running this script, manually copy your ground truth XML files into
the created ground_truth/ directories.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional


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


def create_manifest(
    experiment_dir: Path,
    entry_point: str = "main.xml",
    additional_files: Optional[List[str]] = None,
    ground_truth_dir: str = "ground_truth",
    generated_dir: str = "inputs"
) -> Path:
    """
    Create manifest.json for an experiment.

    Args:
        experiment_dir: Path to experiment directory
        entry_point: Main XML file to compare
        additional_files: Optional list of additional files to compare
        ground_truth_dir: Directory name for ground truth files
        generated_dir: Directory name for generated files

    Returns:
        Path to created manifest.json
    """
    manifest = {
        "entry_point": entry_point,
        "ground_truth_dir": ground_truth_dir,
        "generated_dir": generated_dir
    }

    if additional_files:
        manifest["additional_files"] = additional_files

    # Create ground truth directory
    gt_dir = experiment_dir / ground_truth_dir
    gt_dir.mkdir(parents=True, exist_ok=True)

    # Write manifest
    manifest_path = gt_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return manifest_path


def auto_detect_xml_files(experiment_dir: Path) -> Optional[List[str]]:
    """
    Auto-detect XML files in the inputs directory.

    Args:
        experiment_dir: Path to experiment directory

    Returns:
        List of XML files found, or None if no inputs directory
    """
    inputs_dir = experiment_dir / "inputs"
    if not inputs_dir.exists():
        return None

    xml_files = sorted(inputs_dir.glob("**/*.xml"))
    if not xml_files:
        return None

    # Return relative paths from inputs directory
    return [str(f.relative_to(inputs_dir)) for f in xml_files]


def setup_single_experiment(
    experiment_dir: Path,
    entry_point: Optional[str] = None,
    additional_files: Optional[List[str]] = None,
    auto_detect: bool = False
) -> bool:
    """
    Set up ground truth for a single experiment.

    Args:
        experiment_dir: Path to experiment directory
        entry_point: Main XML file (required unless auto_detect=True)
        additional_files: Optional additional files
        auto_detect: Auto-detect files from inputs directory

    Returns:
        True if successful, False otherwise
    """
    experiment_name = experiment_dir.name

    # Auto-detect if requested
    if auto_detect:
        detected_files = auto_detect_xml_files(experiment_dir)
        if detected_files:
            entry_point = detected_files[0]
            additional_files = detected_files[1:] if len(detected_files) > 1 else None
            print(f"  Auto-detected files: {', '.join(detected_files)}")
        else:
            print(f"{Colors.WARNING}  No XML files found in inputs/, skipping{Colors.ENDC}")
            return False

    # Validate entry point
    if not entry_point:
        print(f"{Colors.FAIL}  Error: entry_point required (or use --auto-detect){Colors.ENDC}")
        return False

    # Create manifest
    try:
        manifest_path = create_manifest(
            experiment_dir,
            entry_point=entry_point,
            additional_files=additional_files
        )

        print(f"{Colors.OKGREEN}  ✓ Created: {manifest_path.relative_to(experiment_dir)}{Colors.ENDC}")

        # Create README
        readme_path = experiment_dir / "ground_truth" / "README.md"
        with open(readme_path, 'w') as f:
            f.write(f"# Ground Truth for {experiment_name}\n\n")
            f.write(f"This directory contains ground truth XML files for evaluation.\n\n")
            f.write(f"## Files to add:\n\n")
            f.write(f"- [ ] `{entry_point}` (entry point)\n")
            if additional_files:
                for file in additional_files:
                    f.write(f"- [ ] `{file}`\n")
            f.write(f"\n## Manifest\n\n")
            f.write(f"See `manifest.json` for evaluation configuration.\n")

        print(f"{Colors.OKGREEN}  ✓ Created: {readme_path.relative_to(experiment_dir)}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}  → Next: Copy ground truth XML files to {experiment_dir / 'ground_truth'}{Colors.ENDC}")

        return True

    except Exception as e:
        print(f"{Colors.FAIL}  ✗ Error: {str(e)}{Colors.ENDC}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Set up ground truth directories for experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Experiment selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--experiment",
        "-e",
        type=Path,
        help="Path to single experiment directory"
    )
    group.add_argument(
        "--experiments-dir",
        "-d",
        type=Path,
        help="Path to experiments directory (batch mode)"
    )

    # File specification
    parser.add_argument(
        "--entry-point",
        type=str,
        help="Main XML file to compare (default: main.xml)"
    )
    parser.add_argument(
        "--additional",
        nargs="+",
        help="Additional files to compare (e.g., imports)"
    )
    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Auto-detect XML files from inputs/ directory"
    )

    args = parser.parse_args()

    # Single experiment mode
    if args.experiment:
        if not args.experiment.exists():
            print(f"{Colors.FAIL}Error: Experiment directory not found: {args.experiment}{Colors.ENDC}")
            sys.exit(1)

        print(f"{Colors.BOLD}Setting up ground truth for: {args.experiment.name}{Colors.ENDC}")
        success = setup_single_experiment(
            args.experiment,
            entry_point=args.entry_point,
            additional_files=args.additional,
            auto_detect=args.auto_detect
        )

        sys.exit(0 if success else 1)

    # Batch mode
    if args.experiments_dir:
        if not args.experiments_dir.exists():
            print(f"{Colors.FAIL}Error: Experiments directory not found: {args.experiments_dir}{Colors.ENDC}")
            sys.exit(1)

        # Find all experiment directories
        experiment_dirs = [d for d in args.experiments_dir.iterdir() if d.is_dir()]

        if not experiment_dirs:
            print(f"{Colors.WARNING}No experiment directories found in {args.experiments_dir}{Colors.ENDC}")
            sys.exit(1)

        print(f"{Colors.BOLD}Setting up ground truth for {len(experiment_dirs)} experiments{Colors.ENDC}\n")

        successes = 0
        for exp_dir in sorted(experiment_dirs):
            print(f"{Colors.OKCYAN}Processing: {exp_dir.name}{Colors.ENDC}")

            # Check if ground truth already exists
            if (exp_dir / "ground_truth" / "manifest.json").exists():
                print(f"{Colors.WARNING}  ⊘ Manifest already exists, skipping{Colors.ENDC}")
                continue

            success = setup_single_experiment(
                exp_dir,
                entry_point=args.entry_point or "main.xml",
                additional_files=args.additional,
                auto_detect=args.auto_detect
            )

            if success:
                successes += 1

            print()  # Blank line between experiments

        # Summary
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ Set up: {successes}/{len(experiment_dirs)} experiments{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
