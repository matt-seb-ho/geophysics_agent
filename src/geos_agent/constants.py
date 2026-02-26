import os
from pathlib import Path

# this file: repo/src/geos_agent/constants.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load environment variables from .env file first (before defining constants)
# This ensures GEOSX_EXECUTABLE and other env vars are available
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # dotenv not installed, use environment variables as-is

# The GEOS-X executable path should be set via GEOSX_EXECUTABLE environment variable
# in your .env file.
GEOSX_EXECUTABLE = Path(os.environ.get("GEOSX_EXECUTABLE", "/usr/local/bin/geosx"))

# Central data directory
DATA_DIR = PROJECT_ROOT / "data"

# Runtime Paths (simulation inputs and outputs)
INPUT_DIR = DATA_DIR / "inputs"
OUTPUT_DIR = DATA_DIR / "outputs"

# GEOS Primer (high-level documentation summary for agent context)
PRIMER_PATH = PROJECT_ROOT / "GEOS_PRIMER.md"

# Dynamic cheatsheet (cross-session memory curated from past trajectories)
CHEATSHEET_PATH = DATA_DIR / "cheatsheet.md"

# Knowledge Base Paths
# GEOS_SOURCE_DIR = DATA_DIR / "geos_source"  # Raw GEOS docs (RST/XML)
GEOS_SOURCE_DIR = Path("/data/shared/geophysics_agent_data/data/GEOS")
GEOSDATA_SOURCE_DIR = Path("/data/shared/geophysics_agent_data/data/GEOSDATA")
CHUNKS_DIR = DATA_DIR / "chunks"            # Processed hierarchical chunks
VECTOR_DB_DIR = DATA_DIR / "vector_db"      # ChromaDB storage
NAV_GRAPH_PATH = DATA_DIR / "nav_graph.json"

# ChromaDB collection names
COLLECTION_NAVIGATOR = "geos_navigator"  # RST prose for navigation
COLLECTION_TECHNICAL = "geos_technical"  # XML schema/tags

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
