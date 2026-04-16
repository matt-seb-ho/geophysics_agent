#!/usr/bin/env python3
"""
Clean experiment subdirectories by removing all files and folders
except inputs/, outputs/, and instructions.txt.

This script operates on all subdirectories in the experiments_subset directory,
located relative to the project root (defined in constants.py).
"""

import os
import shutil
import sys
from pathlib import Path

# Add src to path for importing constants
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from geos_agent.constants import PROJECT_ROOT


def clean_directory_recursive(dir_path: Path, indent: str = "  ") -> int:
    """
    Recursively delete all contents within a directory.
    Returns the count of deleted items.
    """
    deleted_count = 0
    if not dir_path.exists() or not dir_path.is_dir():
        return deleted_count

    try:
        items = list(dir_path.iterdir())
    except (PermissionError, Exception) as e:
        print(f"{indent}Error reading {dir_path.name}: {e}")
        return deleted_count

    for item in items:
        try:
            if item.is_dir():
                # Recursively delete directory contents first
                deleted_count += clean_directory_recursive(item, indent + "  ")
                # Then remove the empty directory
                shutil.rmtree(item)
                print(f"{indent}Deleted directory: {item.name}")
                deleted_count += 1
            else:
                item.unlink()
                print(f"{indent}Deleted file: {item.name}")
                deleted_count += 1
        except PermissionError:
            print(f"{indent}Permission denied (cannot delete): {item.name}")
        except Exception as e:
            print(f"{indent}Error deleting {item.name}: {e}")

    return deleted_count


def clean_experiment_subdir(experiment_dir: Path) -> None:
    """
    Clean a single experiment subdirectory.
    Keep: inputs/, outputs/, instructions.txt (but delete their contents)
    Delete: Everything else recursively
    """
    if not experiment_dir.is_dir():
        print(f"Skipping (not a directory): {experiment_dir}")
        return

    print(f"\nProcessing: {experiment_dir.name}")

    # List of items to preserve at top level
    preserve = {"inputs", "outputs", "instructions.txt"}

    # Get all items in the directory
    try:
        items = list(experiment_dir.iterdir())
    except PermissionError:
        print(f"  Permission denied: {experiment_dir}")
        return
    except Exception as e:
        print(f"  Error reading directory: {e}")
        return

    deleted_count = 0
    for item in items:
        item_name = item.name

        # Skip instructions.txt at top level
        if item_name == "instructions.txt":
            print(f"  Keeping: {item_name}")
            continue

        # Recursively clean inputs/ and outputs/ directories
        if item_name in ("inputs", "outputs") and item.is_dir():
            print(f"  Cleaning: {item_name}/")
            count = clean_directory_recursive(item)
            if count == 0:
                print(f"    (empty)")
            else:
                print(f"    Deleted {count} item(s)")
            continue

        # Delete everything else
        try:
            if item.is_dir():
                shutil.rmtree(item)
                print(f"  Deleted directory: {item_name}")
            else:
                item.unlink()
                print(f"  Deleted file: {item_name}")
            deleted_count += 1
        except PermissionError:
            print(f"  Permission denied (cannot delete): {item_name}")
        except Exception as e:
            print(f"  Error deleting {item_name}: {e}")

    if deleted_count == 0:
        print("  No other files to delete")
    else:
        print(f"  Total deleted from root: {deleted_count} item(s)")


def main():
    """Main function to clean all experiment subdirectories."""
    # Use PROJECT_ROOT from constants.py to find experiments_subset
    base_dir = PROJECT_ROOT / "data" / "eval" / "experiments_subset"

    if not base_dir.exists():
        print(f"Error: Directory does not exist: {base_dir}")
        return 1

    if not base_dir.is_dir():
        print(f"Error: Not a directory: {base_dir}")
        return 1

    print(f"Cleaning experiment subdirectories in: {base_dir}")
    print("=" * 60)

    # Get all subdirectories
    experiment_dirs = [d for d in base_dir.iterdir() if d.is_dir()]

    if not experiment_dirs:
        print("No experiment subdirectories found.")
        return 0

    print(f"Found {len(experiment_dirs)} experiment subdirectory(s)")

    for experiment_dir in sorted(experiment_dirs):
        clean_experiment_subdir(experiment_dir)

    print("\n" + "=" * 60)
    print("Cleaning complete!")
    return 0


if __name__ == "__main__":
    exit(main())
