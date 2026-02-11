"""
Search tools for GEOS documentation RAG.

Two collections:
- Navigator (geos_navigator): RST prose for conceptual navigation
- Technical (geos_technical): XML shadow embeddings for syntax lookup
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from typing import Any, Dict, List
from pathlib import Path
from dotenv import load_dotenv

from .base import Tool

import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.geos_agent.constants import (
    VECTOR_DB_DIR,
    COLLECTION_NAVIGATOR,
    COLLECTION_TECHNICAL,
)

load_dotenv()


def get_embedding_function():
    """Get the embedding function (shared between tools)."""
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        api_base="https://openrouter.ai/api/v1",
        model_name="qwen/qwen3-embedding-8b",
    )


class SearchNavigatorTool(Tool):
    """Search RST prose for conceptual navigation (Collection A)."""
    
    name = "search_navigator"
    description = (
        "Search GEOS documentation for conceptual understanding. "
        "Use this to find which tutorial, guide, or section covers a topic. "
        "Returns document titles, breadcrumbs, and source paths."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language question or topic to search for.",
            },
            "n_results": {
                "type": "integer",
                "description": "Number of results to return (default: 5).",
            },
        },
        "required": ["query"],
    }

    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
        self.embedding_fn = get_embedding_function()
        self.collection = self.client.get_collection(
            name=COLLECTION_NAVIGATOR,
            embedding_function=self.embedding_fn,
        )

    def format_execution_summary(self, query: str, n_results: int = 5, **kwargs) -> str:
        return f"searching documentation for '{query}' (top {n_results} results)"

    def run(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        try:
            # Check for exclusion criteria (RAG contamination prevention)
            excluded_dir = os.environ.get("EXCLUDED_EXAMPLE_DIR", "").lower().strip()

            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2 if excluded_dir else n_results,  # Request more if filtering
            )

            formatted = []
            count = 0
            
            # Retrieve documents
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            if documents and metadatas:
                for i, doc in enumerate(documents):
                    if count >= n_results:
                        break
                        
                    meta = metadatas[i]
                    source_path = meta.get("source_path", "")
                    is_excluded = False
                    
                    # RAG Contamination Filtering
                    if excluded_dir and source_path:
                        try:
                            # e.g., src/docs/sphinx/advancedExamples/validationStudies/carbonStorage/thermalLeakyWell/Example.rst
                            # Parent dir is 'thermalLeakyWell'
                            p = Path(source_path)
                            parent_dir_name = p.parent.name.lower()
                            
                            # Check if parent directory name contains the excluded string (substring match)
                            if excluded_dir in parent_dir_name:
                                is_excluded = True
                        except Exception:
                            pass
                    
                    # For excluded items, we include them but hide the xml_reference
                    # This prevents the agent from easily fetching the full XML source
                    formatted.append({
                        "title": meta.get("title", "No Title"),
                        "breadcrumbs": meta.get("breadcrumbs", ""),
                        "type": meta.get("chunk_type", "unknown"),
                        "source": source_path,
                        "xml_reference": None if is_excluded else meta.get("xml_reference"),
                        "preview": doc[:200] + "..." if len(doc) > 200 else doc,
                        "is_excluded": is_excluded
                    })
                    count += 1

            return {
                "query": query,
                "results": formatted,
                "hint": "Use fetch_code to read the full source file if needed.",
            }

        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}


class SearchTechnicalTool(Tool):
    """Search XML shadow embeddings for syntax lookup (Collection B)."""
    
    name = "search_technical"
    description = (
        "Search for specific XML tags, parameters, or code syntax. "
        "Use this to find exact tag names, attributes, and example usage. "
        "Returns xml_reference pointers for lazy loading with fetch_code."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Technical query: tag name, parameter, or syntax pattern.",
            },
            "n_results": {
                "type": "integer",
                "description": "Number of results to return (default: 5).",
            },
        },
        "required": ["query"],
    }

    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
        self.embedding_fn = get_embedding_function()
        self.collection = self.client.get_collection(
            name=COLLECTION_TECHNICAL,
            embedding_function=self.embedding_fn,
        )

    def format_execution_summary(self, query: str, n_results: int = 5, **kwargs) -> str:
        return f"searching XML/code for '{query}' (top {n_results} results)"

    def run(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
            )

            formatted = []
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                formatted.append({
                    "title": meta["title"],
                    "xml_reference": meta.get("xml_reference", ""),
                    "line_range": meta.get("line_range", ""),
                    "breadcrumbs": meta["breadcrumbs"],
                    "shadow_text": doc[:300] + "..." if len(doc) > 300 else doc,
                })

            return {
                "query": query,
                "results": formatted,
                "hint": "Use fetch_code with xml_reference and line_range to read actual XML.",
            }

        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}


# Legacy compatibility: combined search
class SearchGeosDocsTool(Tool):
    """Combined search across both collections (legacy compatibility)."""
    
    name = "search_geos_docs"
    description = (
        "Search GEOS documentation across both conceptual and technical content. "
        "For precise control, use search_navigator or search_technical instead."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The natural language question or topic to search for.",
            },
        },
        "required": ["query"],
    }

    def __init__(self):
        self.navigator = SearchNavigatorTool()
        self.technical = SearchTechnicalTool()

    def format_execution_summary(self, query: str, **kwargs) -> str:
        return f"searching GEOS docs for '{query}' (combined search)"

    def run(self, query: str) -> Dict[str, Any]:
        nav_results = self.navigator.run(query, n_results=2)
        tech_results = self.technical.run(query, n_results=2)
        
        return {
            "query": query,
            "navigator_results": nav_results.get("results", []),
            "technical_results": tech_results.get("results", []),
            "hint": "Use search_navigator for concepts, search_technical for syntax.",
        }


class SearchWebTool(Tool):
    """Web search stub (not yet implemented)."""
    
    name = "search_web"
    description = "Search the web for relevant information. Currently a stub."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Web search query.",
            },
        },
        "required": ["query"],
    }

    def format_execution_summary(self, query: str, **kwargs) -> str:
        return f"web searching for '{query}'"

    def run(self, query: str) -> Dict[str, Any]:
        # TODO
        return {
            "query": query,
            "warning": "search_web is not yet implemented in this environment.",
        }
