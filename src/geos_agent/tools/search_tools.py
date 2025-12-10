from pathlib import Path
from typing import Any, Dict

from .base import Tool

# ==============================
# Stub tools for GEOS + search
# ==============================


class SearchGeosDocsTool(Tool):
    name = "search_geos_docs"
    description = (
        "Search the GEOS / GEOSX documentation for relevant information. "
        "Currently a stub: it returns a placeholder message."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for the GEOS documentation.",
            }
        },
        "required": ["query"],
    }

    def run(self, query: str) -> Dict[str, Any]:
        # TODO: implement real doc search (e.g., RAG over docs)
        return {
            "query": query,
            "warning": "search_geos_docs is not yet implemented. "
            "Please browse docs manually for now.",
        }


class SearchWebTool(Tool):
    name = "search_web"
    description = (
        "Search the web for relevant information. "
        "Currently a stub: it returns a placeholder message."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Web search query.",
            }
        },
        "required": ["query"],
    }

    def run(self, query: str) -> Dict[str, Any]:
        # TODO: wire up to a real web search / RAG
        return {
            "query": query,
            "warning": "search_web is not yet implemented in this environment.",
        }


class RunGeosTool(Tool):
    name = "run_geos"
    description = (
        "Run a GEOS simulation given an input configuration file. "
        "Currently a stub until GEOS is compiled and available."
    )
    parameters = {
        "type": "object",
        "properties": {
            "input_path": {
                "type": "string",
                "description": "Path to the GEOS input file (relative to workspace).",
            },
            "extra_args": {
                "type": "string",
                "description": (
                    "Additional command-line arguments for GEOS, if needed."
                ),
                "default": "",
            },
        },
        "required": ["input_path"],
    }

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()

    def run(self, input_path: str, extra_args: str = "") -> Dict[str, Any]:
        # TODO: once GEOS is compiled, call the real binary here via subprocess.
        return {
            "input_path": input_path,
            "extra_args": extra_args,
            "warning": "run_geos is currently stubbed; GEOS is not yet wired up.",
        }
