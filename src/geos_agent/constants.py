from pathlib import Path

# this file: repo/src/geos_agent/constants.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Central data directory
DATA_DIR = PROJECT_ROOT / "data"

# Runtime Paths (simulation inputs and outputs)
INPUT_DIR = DATA_DIR / "inputs"
OUTPUT_DIR = DATA_DIR / "outputs"

# Knowledge Base Paths (RAG documentation pipeline)
SOURCE_DOCS_DIR = DATA_DIR / "source"
PROCESSED_DOCS_DIR = DATA_DIR / "processed"
VECTOR_INDEX_DIR = DATA_DIR / "vector_index"

# Processed documentation subdirectories
CONCEPTS_DIR = PROCESSED_DOCS_DIR / "concepts"
EXAMPLES_DIR = PROCESSED_DOCS_DIR / "examples"

# Ensure strict existence of critical directories
for path in [
    INPUT_DIR,
    OUTPUT_DIR,
    SOURCE_DOCS_DIR,
    PROCESSED_DOCS_DIR,
    VECTOR_INDEX_DIR,
    CONCEPTS_DIR,
    EXAMPLES_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)
