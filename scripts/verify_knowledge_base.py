#!/usr/bin/env python3
"""
Verify that the knowledge base has been properly built.

Usage:
    python scripts/verify_knowledge_base.py
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.geos_agent.constants import (
    CONCEPTS_DIR,
    EXAMPLES_DIR,
    PROCESSED_DOCS_DIR,
    SOURCE_DOCS_DIR,
    VECTOR_INDEX_DIR,
)


def check_directory(path: Path, name: str) -> bool:
    """Check if a directory exists."""
    if path.exists() and path.is_dir():
        print(f"✓ {name} exists: {path}")
        return True
    else:
        print(f"✗ {name} missing: {path}")
        return False


def count_files(path: Path, pattern: str) -> int:
    """Count files matching pattern."""
    if not path.exists():
        return 0
    return len(list(path.rglob(pattern)))


def verify_knowledge_base() -> bool:
    """
    Verify the knowledge base structure and contents.

    Returns:
        True if verification passes, False otherwise
    """
    print("=" * 60)
    print("GEOS Agent Knowledge Base Verification")
    print("=" * 60)

    all_good = True

    # Check directories
    print("\n1. Checking Directory Structure:")
    print("-" * 60)
    all_good &= check_directory(SOURCE_DOCS_DIR, "Source docs")
    all_good &= check_directory(PROCESSED_DOCS_DIR, "Processed docs")
    all_good &= check_directory(CONCEPTS_DIR, "Concepts")
    all_good &= check_directory(EXAMPLES_DIR, "Examples")
    all_good &= check_directory(VECTOR_INDEX_DIR, "Vector index")

    # Check llms.txt
    print("\n2. Checking Master Index:")
    print("-" * 60)
    llms_txt = PROCESSED_DOCS_DIR / "llms.txt"
    if llms_txt.exists():
        print(f"✓ llms.txt exists: {llms_txt}")
        lines = llms_txt.read_text().split("\n")
        print(f"  Contains {len(lines)} lines")
    else:
        print(f"✗ llms.txt missing: {llms_txt}")
        all_good = False

    # Count files
    print("\n3. Counting Content Files:")
    print("-" * 60)

    # Count source RST files
    source_rst_count = count_files(SOURCE_DOCS_DIR, "*.rst")
    print(f"Source RST files: {source_rst_count}")
    if source_rst_count < 50:
        print(f"  ⚠ Warning: Expected ~115 RST files, found {source_rst_count}")
        print(f"  You may need to rebuild with --geos-repo option")

    # Count concept files
    concept_count = count_files(CONCEPTS_DIR, "*.md")
    print(f"Concept files: {concept_count}")
    if concept_count < 300:
        print(f"  ⚠ Warning: Expected ~388 concepts, found {concept_count}")
        all_good = False
    elif concept_count == 388:
        print(f"  ✓ Perfect! Expected 388 concepts")
    else:
        print(f"  ✓ Good (expected ~388)")

    # Count example files
    example_count = count_files(EXAMPLES_DIR, "*.md")
    print(f"Example files: {example_count}")
    if example_count < 5:
        print(f"  ⚠ Warning: Expected ~7 example files, found {example_count}")
        all_good = False
    elif example_count == 7:
        print(f"  ✓ Perfect! Expected 7 example files")
    else:
        print(f"  ✓ Good (expected ~7)")

    # Check for XML in examples
    print("\n4. Checking Example Quality:")
    print("-" * 60)
    examples_with_xml = 0
    for example_file in EXAMPLES_DIR.rglob("*.md"):
        content = example_file.read_text()
        if "```xml" in content and "<!-- XML file not found -->" not in content:
            examples_with_xml += 1

    print(f"Examples with XML: {examples_with_xml}/{example_count}")
    if examples_with_xml < example_count:
        missing = example_count - examples_with_xml
        print(f"  ⚠ Warning: {missing} example(s) missing XML content")
        print(f"  Check that inputFiles/ was copied from GEOS repo")
    else:
        print(f"  ✓ All examples have XML inlined")

    # Summary
    print("\n" + "=" * 60)
    if all_good and concept_count >= 300 and example_count >= 5:
        print("✓ Knowledge Base Verification PASSED")
        print("=" * 60)
        print("\nYour knowledge base is ready to use!")
        return True
    else:
        print("✗ Knowledge Base Verification FAILED")
        print("=" * 60)
        print("\nPlease rebuild the knowledge base:")
        print("  python scripts/build_knowledge.py --geos-repo /path/to/GEOS")
        return False


if __name__ == "__main__":
    success = verify_knowledge_base()
    sys.exit(0 if success else 1)
