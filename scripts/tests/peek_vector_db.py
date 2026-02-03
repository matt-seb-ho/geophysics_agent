#!/usr/bin/env python3
"""Peek at the contents of the ChromaDB vector database."""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import chromadb


def main():
    db_path = PROJECT_ROOT / "data" / "vector_db"
    
    if not db_path.exists():
        print(f"[error] Vector database not found at: {db_path}")
        return
    
    client = chromadb.PersistentClient(path=str(db_path))
    collections = client.list_collections()
    
    print(f"Found {len(collections)} collection(s):\n")
    
    for collection in collections:
        print("=" * 60)
        print(f"Collection: {collection.name}")
        print(f"Count: {collection.count()} documents")
        print("=" * 60)
        
        # Peek at sample documents
        results = collection.peek(limit=20)
        
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                print(f"\n--- Document {i + 1} ---")
                print(f"ID: {doc_id}")
                
                if results["metadatas"] and results["metadatas"][i]:
                    print(f"Metadata: {results['metadatas'][i]}")
                
                if results["documents"] and results["documents"][i]:
                    doc = results["documents"][i]
                    # Truncate long documents
                    preview = doc[:500] + "..." if len(doc) > 500 else doc
                    print(f"Content:\n{preview}")
        else:
            print("(empty collection)")
        
        print()


if __name__ == "__main__":
    main()
