# scripts/build_vector_index.py
import os
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
from dotenv import load_dotenv

# Load env vars (for OpenAI API Key)
load_dotenv()

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
VECTOR_DB_PATH = PROJECT_ROOT / "data" / "vector_index"
COLLECTION_NAME = "geos_docs"

def build_index():
    print(f"Building vector index in: {VECTOR_DB_PATH}")
    
    # 1. Initialize ChromaDB (Persistent means it saves to disk)
    client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
    
    # 2. Use OpenAI for embeddings (matches your agent's intelligence)
    # Ensure OPENROUTER_API_KEY is in your .env
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ["OPENROUTER_API_KEY"], # Use OpenRouter Key
        api_base="https://openrouter.ai/api/v1",   # Point to OpenRouter
        model_name="qwen/qwen3-embedding-8b"        # Use a supported model
    )

    # 3. Create or Reset the Collection
    # We delete it first to ensure we don't have stale data
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except chromadb.errors.NotFoundError:
        pass # Collection didn't exist
    
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=openai_ef
    )

    # 4. Crawl and Index
    documents = []
    metadatas = []
    ids = []

    # Helper to process a directory
    def process_dir(directory: Path, category: str):
        if not directory.exists():
            print(f"Skipping {directory} (not found)")
            return

        for file_path in directory.glob("**/*.md"):
            print(f"Indexing: {file_path.name}")
            text = file_path.read_text(encoding="utf-8")
            
            # Create a clean ID
            doc_id = str(file_path.relative_to(PROCESSED_DIR))
            
            documents.append(text)
            metadatas.append({"source": str(file_path), "category": category})
            ids.append(doc_id)

    # Index Concepts and Examples
    process_dir(PROCESSED_DIR / "concepts", "concept")
    process_dir(PROCESSED_DIR / "examples", "example")

    # 5. Add to Database
    if documents:
        print(f"Adding {len(documents)} documents to vector store...")
        # Add in batches of 100 to be safe
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            collection.add(
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
                ids=ids[i : i + batch_size]
            )
        print("Done! Index saved.")
    else:
        print("No documents found in data/processed!")

if __name__ == "__main__":
    build_index()