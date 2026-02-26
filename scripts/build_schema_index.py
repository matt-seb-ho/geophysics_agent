#!/usr/bin/env python3
"""
Build the geos_schema ChromaDB collection from parsed XSD schema chunks.

Usage:
    uv run python scripts/build_schema_index.py
    uv run python scripts/build_schema_index.py --chunks data/chunks/schema/chunks.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.geos_agent.constants import (
    COLLECTION_SCHEMA,
    SCHEMA_CHUNKS_DIR,
    VECTOR_DB_DIR,
)

load_dotenv()


def build_schema_collection(chunks_path: Path) -> int:
    """Build the geos_schema ChromaDB collection from schema chunks JSON."""

    if not chunks_path.exists():
        print(f"[error] Chunks file not found: {chunks_path}")
        print("  Run:  uv run python scripts/parse_xsd_schema.py  first.")
        return 0

    with open(chunks_path) as f:
        chunks = json.load(f)

    print(f"  Loaded {len(chunks)} schema chunks")

    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[error] OPENROUTER_API_KEY or OPENAI_API_KEY not set")
        return 0

    embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        api_base="https://openrouter.ai/api/v1",
        model_name="qwen/qwen3-embedding-8b",
    )

    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))

    # Drop and recreate
    try:
        client.delete_collection(name=COLLECTION_SCHEMA)
        print(f"  Deleted existing '{COLLECTION_SCHEMA}' collection")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_SCHEMA,
        embedding_function=embedding_fn,
    )

    documents, metadatas, ids = [], [], []

    for chunk in chunks:
        documents.append(chunk["embedding_text"])
        ids.append(chunk["chunk_id"])
        # Store flat metadata (ChromaDB requires str/int/float/bool values)
        attr_names = ",".join(a["name"] for a in chunk["attributes"])
        metadatas.append({
            "chunk_type":      chunk["chunk_type"],
            "element_name":    chunk["element_name"],
            "type_name":       chunk["type_name"],
            "attribute_names": attr_names,
            "attribute_count": len(chunk["attributes"]),
            "source_path":     chunk["source_path"],
            "title":           chunk["title"],
            "breadcrumbs":     chunk["breadcrumbs"],
        })

    batch_size = 50
    for i in range(0, len(documents), batch_size):
        end = min(i + batch_size, len(documents))
        batch_num = i // batch_size + 1
        total_batches = (len(documents) - 1) // batch_size + 1
        print(f"  Adding batch {batch_num}/{total_batches}...")
        collection.add(
            documents=documents[i:end],
            metadatas=metadatas[i:end],
            ids=ids[i:end],
        )

    print(f"  ✓ Added {len(documents)} documents to '{COLLECTION_SCHEMA}'")
    return len(documents)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build geos_schema ChromaDB collection")
    parser.add_argument(
        "--chunks", type=Path,
        default=SCHEMA_CHUNKS_DIR / "chunks.json",
        help="Path to schema chunks.json",
    )
    args = parser.parse_args()

    print(f"=== Building '{COLLECTION_SCHEMA}' Collection ===")
    print(f"Vector DB: {VECTOR_DB_DIR}")
    count = build_schema_collection(args.chunks)
    if count:
        print(f"\nDone — {count} schema chunks indexed.")


if __name__ == "__main__":
    main()
