import os
import chromadb
from chromadb.utils import embedding_functions
from typing import Any, Dict
from pathlib import Path
from dotenv import load_dotenv

from .base import Tool

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VECTOR_DB_PATH = PROJECT_ROOT / "data" / "vector_index"
COLLECTION_NAME = "geos_docs"

# NOTE: web search currently stubs; to be implemented later.


class SearchGeosDocsTool(Tool):
    name = "search_geos_docs"
    description = (
        "Search the GEOS documentation for concepts, examples, and XML syntax. "
        "Returns the most relevant text chunks from the documentation."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The natural language question or topic to search for.",
            }
        },
        "required": ["query"],
    }

    def __init__(self):
        # Initialize connection once when tool is created
        self.client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        
        # Must match the embedding function used in the build script
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY"),
            api_base="https://openrouter.ai/api/v1",  # Must match build script
            model_name="qwen/qwen3-embedding-8b"
        )
        self.collection = self.client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=self.openai_ef
        )

    def run(self, query: str) -> Dict[str, Any]:
        try:
            # Retrieve top 3 most relevant matches
            results = self.collection.query(
                query_texts=[query],
                n_results=3
            )

            # Format results for the Agent to read
            formatted_results = []
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                formatted_results.append(f"--- Result {i+1} (Source: {meta['source']}) ---\n{doc}\n")

            return {
                "query": query,
                "results": "\n".join(formatted_results)
            }

        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

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
