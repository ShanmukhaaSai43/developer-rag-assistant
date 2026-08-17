"""
===================================================================
STEP 4: Vector Database & HNSW Graph Indexing
===================================================================
GOAL: Store embedded chunks and metadata into a local Vector Store
      powered by HNSW (Hierarchical Navigable Small World) indexing.

Key Concepts:
- Vector Database: Stores (1) Vector Embeddings, (2) Document Text, (3) Metadata.
- HNSW Index: Multi-layer graph algorithm for sub-millisecond similarity search.
- ChromaDB / Persistent Store: Persists indexed vectors to local disk (.chroma_db/).
"""

import importlib.util
from pathlib import Path
import numpy as np

# Dynamically import Step 1, Step 2, and Step 3 modules
DOCS_DIR = Path(__file__).parent.parent / "docs"
step1_path = Path(__file__).parent / "01_ingest_docs.py"
step2_path = Path(__file__).parent / "02_chunk_docs.py"
step3_path = Path(__file__).parent / "03_embed_docs.py"

spec1 = importlib.util.spec_from_file_location("step1_module", step1_path)
step1_module = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(step1_module)

spec2 = importlib.util.spec_from_file_location("step2_module", step2_path)
step2_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(step2_module)

spec3 = importlib.util.spec_from_file_location("step3_module", step3_path)
step3_module = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(step3_module)

load_markdown_documents = step1_module.load_markdown_documents
chunk_document_by_sections = step2_module.chunk_document_by_sections
BGETextEmbeddingGenerator = getattr(step3_module, "BGETextEmbeddingGenerator", step3_module.GeminiNeuralEmbeddingGenerator)
GeminiNeuralEmbeddingGenerator = step3_module.GeminiNeuralEmbeddingGenerator

# Try importing ChromaDB
try:
    import os
    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


class LocalVectorStoreHNSW:
    """
    Manages vector storage, HNSW indexing, and metadata persistence.
    Uses ChromaDB PersistentClient when available, falls back to NumPy.
    """
    def __init__(self, collection_name: str = "developer_docs_hnsw"):
        self.collection_name = collection_name
        self.use_chromadb = False
        print(f"[STEP 4 - VECTOR DB] Initializing Vector Store Collection '{collection_name}'...")

        if HAS_CHROMADB:
            # Initialize local persistent ChromaDB client
            chroma_dir = Path(__file__).parent.parent / ".chroma_db"
            self.client = chromadb.PersistentClient(path=str(chroma_dir))

            # Get or create collection (cosine similarity for HNSW space)
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.use_chromadb = True
            print(f"✅ Persistent ChromaDB initialized at: {chroma_dir}")
        else:
            # Pure-Python fallback: numpy-based cosine similarity search
            self.ids = []
            self.vectors = []
            self.documents = []
            self.metadatas = []
            print("✅ NumPy in-memory vector store initialized (ChromaDB not available).")

    def add_chunks(self, embedded_chunks: list[dict]):
        """
        Indexes chunks into the Vector DB with vectors, document text, and metadata.
        """
        print(f"Indexing {len(embedded_chunks)} embedded chunk(s) into HNSW index...")

        ids = [str(c["chunk_id"]) for c in embedded_chunks]
        vectors = [c["vector"] for c in embedded_chunks]
        documents = [str(c["content"]) for c in embedded_chunks]
        metadatas = [
            {
                "source_file": str(c["source_file"]),
                "recipe_id": str(c.get("recipe_id", "")),
                "cuisine": str(c.get("cuisine", "")),
                "dietary_tags": str(c.get("dietary_tags", "")),
                "section_title": str(c["section_title"]),
                "char_count": int(c["char_count"])
            }
            for c in embedded_chunks
        ]

        if self.use_chromadb:
            self.collection.upsert(
                ids=ids,
                embeddings=vectors,
                documents=documents,
                metadatas=metadatas
            )
            print(f"✅ Successfully indexed {len(ids)} items into ChromaDB HNSW store!")
        else:
            self.ids.extend(ids)
            self.vectors.extend(vectors)
            self.documents.extend(documents)
            self.metadatas.extend(metadatas)
            print(f"✅ Successfully indexed {len(ids)} items into NumPy vector store!")

    def query(self, query_embeddings: list, n_results: int = 2, where: dict = None) -> dict:
        """
        Vector similarity search — returns results in ChromaDB-compatible format.
        Uses ChromaDB HNSW when available, otherwise pure NumPy cosine similarity.

        Returns dict with keys: ids, documents, metadatas, distances
        (distances = 1.0 - similarity for cosine space, so lower = better match)
        """
        if self.use_chromadb:
            query_kwargs = {
                "query_embeddings": query_embeddings,
                "n_results": n_results
            }
            if where:
                query_kwargs["where"] = where
            return self.collection.query(**query_kwargs)

        # Pure numpy cosine similarity fallback
        query_vec = np.array(query_embeddings[0])
        all_vecs = np.array(self.vectors)

        # Cosine similarity = dot(a, b) / (||a|| * ||b||)
        dot_products = np.dot(all_vecs, query_vec)
        norms = np.linalg.norm(all_vecs, axis=1) * np.linalg.norm(query_vec)
        similarities = dot_products / (norms + 1e-10)

        # Apply metadata filter if provided
        valid_indices = list(range(len(self.ids)))
        if where:
            valid_indices = [
                i for i in valid_indices
                if all(self.metadatas[i].get(k) == v for k, v in where.items())
            ]

        # Sort by similarity (highest first), pick top n_results
        scored = [(i, float(similarities[i])) for i in valid_indices]
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:n_results]

        # Return in ChromaDB response format (distances = 1 - similarity for cosine)
        return {
            "ids": [[self.ids[i] for i, _ in top]],
            "documents": [[self.documents[i] for i, _ in top]],
            "metadatas": [[self.metadatas[i] for i, _ in top]],
            "distances": [[1.0 - s for _, s in top]]
        }

    def count(self) -> int:
        """Returns total number of indexed vectors."""
        if self.use_chromadb:
            return self.collection.count()
        return len(self.ids)


if __name__ == "__main__":
    print("=== STEP 4: VECTOR DATABASE & HNSW INDEXING TEST ===\n")
    
    docs = load_markdown_documents(DOCS_DIR)
    
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document_by_sections(doc))
        
    embedder = BGETextEmbeddingGenerator(model_name="BAAI/bge-small-en-v1.5")
    embedded_chunks = embedder.generate_embeddings(all_chunks)
    
    vector_db = LocalVectorStoreHNSW(collection_name="developer_docs_hnsw")
    vector_db.add_chunks(embedded_chunks)
    
    print(f"\n✅ Step 4 Complete!")
    print(f"Total Vectors Indexed in Vector Store: {vector_db.count()}")
    print("Ready for Step 5: Similarity Search & Top-K Retrieval!")
