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
    COLLECTION_SCHEMA,
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
                    
                    formatted.append({
                        "title": meta.get("title", "No Title"),
                        "breadcrumbs": meta.get("breadcrumbs", ""),
                        "type": meta.get("chunk_type", "unknown"),
                        "source": source_path,
                        "preview": doc[:200] + "..." if len(doc) > 200 else doc,
                        "is_excluded": is_excluded,
                    })
                    count += 1

            return {
                "query": query,
                "results": formatted,
                "hint": "Use read_file with path (+ optional line/marker params) for full source content.",
            }

        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}


class SearchTechnicalTool(Tool):
    """Search XML shadow embeddings for syntax lookup (Collection B)."""
    
    name = "search_technical"
    description = (
        "Search for specific XML tags, parameters, or code syntax. "
        "Use this to find exact tag names, attributes, and example usage. "
        "Returns xml_reference pointers for lazy loading with read_file."
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
            # Check for exclusion criteria (RAG contamination prevention)
            excluded_dir = os.environ.get("EXCLUDED_EXAMPLE_DIR", "").lower().strip()

            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2 if excluded_dir else n_results,
            )

            formatted = []
            count = 0
            for i, doc in enumerate(results["documents"][0]):
                if count >= n_results:
                    break

                meta = results["metadatas"][0][i]
                xml_ref = meta.get("xml_reference") or ""
                source_path = meta.get("source_path", "")
                is_excluded = False

                # RAG Contamination Filtering: check xml_reference and source_path
                if excluded_dir and (xml_ref or source_path):
                    try:
                        for check_path in (xml_ref, source_path):
                            if check_path:
                                p = Path(check_path)
                                if excluded_dir in str(p.parent).lower():
                                    is_excluded = True
                                    break
                    except Exception:
                        pass

                formatted.append({
                    "title": meta["title"],
                    "xml_reference": None if is_excluded else xml_ref,
                    "line_range": meta.get("line_range", ""),
                    "breadcrumbs": meta["breadcrumbs"],
                    "source_path": source_path,
                    "shadow_text": doc[:300] + "..." if len(doc) > 300 else doc,
                    "is_excluded": is_excluded,
                })
                count += 1

            return {
                "query": query,
                "results": formatted,
                "hint": "Use read_file with path and start_line/end_line or markers to read actual XML.",
            }

        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}


class SearchSchemaTool(Tool):
    """Search the GEOS XML schema for element attribute specifications (Collection C)."""

    name = "search_schema"
    description = (
        "Look up the exact attributes, types, defaults, and descriptions for any "
        "GEOS XML element. Use this when you need to know what parameters an element "
        "accepts, their types, default values, or what they mean. "
        "Returns the full attribute spec for matching elements — no follow-up file read needed."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Element name or attribute description to look up. "
                    "Examples: 'ViscoDruckerPrager', 'targetRegions solver', "
                    "'relaxation time constitutive', 'mesh nx ny nz'."
                ),
            },
            "n_results": {
                "type": "integer",
                "description": "Number of element specs to return (default: 3).",
            },
        },
        "required": ["query"],
    }

    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
        self.embedding_fn = get_embedding_function()
        self.collection = self.client.get_collection(
            name=COLLECTION_SCHEMA,
            embedding_function=self.embedding_fn,
        )

    def format_execution_summary(self, query: str, n_results: int = 3, **kwargs) -> str:
        return f"looking up XML schema for '{query}' (top {n_results})"

    def run(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            formatted = []
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                # The document IS the full human-readable spec — return it directly.
                formatted.append({
                    "element": meta["element_name"],
                    "title": meta["title"],
                    "attribute_count": meta["attribute_count"],
                    "spec": doc,          # full attribute listing
                    "relevance": round(1 - dist, 4),
                })

            return {
                "query": query,
                "results": formatted,
                "hint": (
                    "The 'spec' field contains all attributes with types, defaults, "
                    "and descriptions. Use this to write the XML element correctly."
                ),
            }

        except Exception as e:
            return {"error": f"Schema search failed: {str(e)}"}


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
