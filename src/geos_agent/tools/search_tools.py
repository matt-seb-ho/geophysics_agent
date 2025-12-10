from typing import Any, Dict

from .base import Tool


# NOTE: currently stubs; to be implemented later.


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
