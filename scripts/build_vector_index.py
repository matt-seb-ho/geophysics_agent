#!/usr/bin/env python3
"""
Build dual ChromaDB vector indexes from parsed chunks.

Creates two collections:
- geos_navigator: RST prose for conceptual navigation
- geos_technical: XML shadow embeddings for syntax lookup

Usage:
    python scripts/build_vector_index.py
"""

import json
import os
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
from dotenv import load_dotenv

import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.geos_agent.constants import (
    VECTOR_DB_DIR,
    NAVIGATOR_CHUNKS_DIR,
    TECHNICAL_CHUNKS_DIR,
    COLLECTION_NAVIGATOR,
    COLLECTION_TECHNICAL,
)

load_dotenv()


def build_collection(
    client: chromadb.PersistentClient,
    collection_name: str,
    chunks_path: Path,
    embedding_fn,
) -> int:
    """Build a single ChromaDB collection from chunks JSON."""
    
    print(f"\nBuilding collection: {collection_name}")
    
    # Load chunks
    if not chunks_path.exists():
        print(f"  [skip] Chunks file not found: {chunks_path}")
        return 0
    
    with open(chunks_path) as f:
        chunks = json.load(f)
    
    print(f"  Loaded {len(chunks)} chunks")
    
    # Delete existing collection if exists
    try:
        client.delete_collection(name=collection_name)
        print(f"  Deleted existing collection")
    except Exception:
        pass
    
    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
    )
    
    # Prepare data for insertion
    documents = []
    metadatas = []
    ids = []
    
    for chunk in chunks:
        documents.append(chunk["embedding_text"])
        ids.append(chunk["chunk_id"])
        
        # Store rich metadata for retrieval.
        # xml_reference is only present for technical chunks (always null in navigator).
        meta = {
            "chunk_type": chunk["chunk_type"],
            "source_path": chunk["source_path"],
            "parent_id": chunk.get("parent_id") or "",
            "title": chunk["title"],
            "breadcrumbs": chunk["breadcrumbs"],
            "line_range": chunk.get("line_range") or "",
        }
        if chunk.get("xml_reference"):
            meta["xml_reference"] = chunk["xml_reference"]
        metadatas.append(meta)
    
    # Add in batches
    batch_size = 50
    for i in range(0, len(documents), batch_size):
        end_idx = min(i + batch_size, len(documents))
        print(f"  Adding batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}...")
        
        collection.add(
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx],
        )
    
    print(f"  ✓ Added {len(documents)} documents to {collection_name}")
    return len(documents)


def build_indexes():
    """Main function to build both vector indexes."""
    
    print(f"=== Building Vector Indexes ===")
    print(f"Vector DB path: {VECTOR_DB_DIR}")
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    
    # Initialize embedding function (matching model from original)
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[error] OPENROUTER_API_KEY or OPENAI_API_KEY not found in environment")
        return
    
    embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        api_base="https://openrouter.ai/api/v1",
        model_name="qwen/qwen3-embedding-8b",
    )
    
    # Build Navigator collection (RST prose)
    nav_count = build_collection(
        client,
        COLLECTION_NAVIGATOR,
        NAVIGATOR_CHUNKS_DIR / "chunks.json",
        embedding_fn,
    )
    
    # Build Technical collection (XML shadow embeddings)
    tech_count = build_collection(
        client,
        COLLECTION_TECHNICAL,
        TECHNICAL_CHUNKS_DIR / "chunks.json",
        embedding_fn,
    )
    
    print("\n=== Vector Index Build Complete ===")
    print(f"Navigator collection: {nav_count} documents")
    print(f"Technical collection: {tech_count} documents")


if __name__ == "__main__":
    build_indexes()