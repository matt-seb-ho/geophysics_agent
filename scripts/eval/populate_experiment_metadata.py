#!/usr/bin/env python3
"""
Populate metadata.json in experiment directories from example_pairs.jsonl.

Writes a metadata.json into each experiment folder containing the rst_path
(source RST document path) needed for RAG retrieval accuracy evaluation.

Usage:
    # Populate metadata for all experiment directories
    uv run python scripts/eval/populate_experiment_metadata.py

    # Populate a specific experiments directory
    uv run python scripts/eval/populate_experiment_metadata.py \
        --experiments-dir data/eval/experiments_subset
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Add src to path for constants
sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
from geos_agent.constants import DATA_DIR


def clean_title(title: str) -> str:
    """Remove all non-alphanumeric characters from a title."""
    return re.sub(r'[^a-zA-Z0-9]', '', title)


def load_experiment_data(jsonl_path: Path) -> dict:
    """Load example_pairs.jsonl into a dict keyed by cleaned experiment name."""
    data = {}
    with open(jsonl_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            title = entry.get('title', '')
            cleaned = clean_title(title)
            data[cleaned] = entry
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Populate metadata.json in experiment directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--experiments-dir",
        type=Path,
        nargs="+",
        default=None,
        help="Experiment directories to populate (default: experiments/ and experiments_subset/)"
    )
    parser.add_argument(
        "--jsonl",
        type=Path,
        default=None,
        help="Path to example_pairs.jsonl (default: data/eval/example_pairs.jsonl)"
    )

    args = parser.parse_args()

    jsonl_path = args.jsonl or DATA_DIR / "eval" / "example_pairs.jsonl"
    if not jsonl_path.exists():
        print(f"Error: {jsonl_path} not found")
        sys.exit(1)

    # Default: populate both experiments/ and experiments_subset/
    if args.experiments_dir:
        experiment_dirs = args.experiments_dir
    else:
        experiment_dirs = [
            DATA_DIR / "eval" / "experiments",
            DATA_DIR / "eval" / "experiments_subset",
        ]

    # Load the mapping
    experiments_data = load_experiment_data(jsonl_path)
    print(f"Loaded {len(experiments_data)} entries from {jsonl_path}")

    total_written = 0
    total_skipped = 0

    for exp_base_dir in experiment_dirs:
        if not exp_base_dir.exists():
            print(f"Skipping (not found): {exp_base_dir}")
            continue

        print(f"\nProcessing: {exp_base_dir}")

        for exp_dir in sorted(exp_base_dir.iterdir()):
            if not exp_dir.is_dir():
                continue

            exp_name = exp_dir.name
            if exp_name not in experiments_data:
                print(f"  {exp_name}: no match in jsonl, skipping")
                total_skipped += 1
                continue

            entry = experiments_data[exp_name]
            metadata = {
                "rst_path": entry.get("rst_path", ""),
            }

            metadata_path = exp_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"  {exp_name}: wrote metadata.json (rst_path: {metadata['rst_path']})")
            total_written += 1

    print(f"\nDone. Wrote {total_written} metadata files, skipped {total_skipped}.")


if __name__ == "__main__":
    main()
