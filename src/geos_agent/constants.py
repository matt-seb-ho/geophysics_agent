from pathlib import Path

# this file: repo/src/geos_agent/constants.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Central data directory
DATA_DIR = PROJECT_ROOT / "data"

# Runtime Paths (simulation inputs and outputs)
INPUT_DIR = DATA_DIR / "inputs"
OUTPUT_DIR = DATA_DIR / "outputs"

# Knowledge Base Paths
# GEOS_SOURCE_DIR = DATA_DIR / "geos_source"  # Raw GEOS docs (RST/XML)
GEOS_SOURCE_DIR = PROJECT_ROOT.parent.parent.parent / "data" / "brianliu" # point to ad hoc data source (brianliu) 
CHUNKS_DIR = DATA_DIR / "chunks"            # Processed hierarchical chunks
VECTOR_DB_DIR = DATA_DIR / "vector_db"      # ChromaDB storage
NAV_GRAPH_PATH = DATA_DIR / "nav_graph.json"

# ChromaDB collection names
COLLECTION_NAVIGATOR = "geos_navigator"     # RST prose for navigation
COLLECTION_TECHNICAL = "geos_technical"     # XML schema/tags

# Processed chunk subdirectories
NAVIGATOR_CHUNKS_DIR = CHUNKS_DIR / "navigator"
TECHNICAL_CHUNKS_DIR = CHUNKS_DIR / "technical"

# Ensure critical directories exist
for path in [
    INPUT_DIR,
    OUTPUT_DIR,
    GEOS_SOURCE_DIR,
    CHUNKS_DIR,
    VECTOR_DB_DIR,
    NAVIGATOR_CHUNKS_DIR,
    TECHNICAL_CHUNKS_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)
