"""
===================================================================
STEP 5: Dense Retrieval, Similarity Search & Top-K Filtering
===================================================================
GOAL: Query the Vector Store for user questions, convert queries to 
      neural vectors, perform Cosine Similarity search, and filter Top-K results.

Key Concepts:
- Dense Retrieval: Converts query text into a vector and searches HNSW graph.
- Cosine Distance to Similarity: Score = 1.0 - distance (Higher is better!).
- Top-K Filtering: Returns top K matching chunks (e.g., top_k=2).
- Metadata Filtering: Restricts search by file or section (e.g. where={"source_file": "..."}).
"""

import importlib.util
from pathlib import Path
import numpy as np

# Dynamically import Step 1, Step 2, Step 3, and Step 4 modules
DOCS_DIR = Path(__file__).parent.parent / "docs"
step1_path = Path(__file__).parent / "01_ingest_docs.py"
step2_path = Path(__file__).parent / "02_chunk_docs.py"
step3_path = Path(__file__).parent / "03_embed_docs.py"
step4_path = Path(__file__).parent / "04_vector_db.py"

spec1 = importlib.util.spec_from_file_location("step1_module", step1_path)
step1_module = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(step1_module)

spec2 = importlib.util.spec_from_file_location("step2_module", step2_path)
step2_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(step2_module)

spec3 = importlib.util.spec_from_file_location("step3_module", step3_path)
step3_module = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(step3_module)

spec4 = importlib.util.spec_from_file_location("step4_module", step4_path)
step4_module = importlib.util.module_from_spec(spec4)
spec4.loader.exec_module(step4_module)

load_markdown_documents = step1_module.load_markdown_documents
chunk_document_by_sections = step2_module.chunk_document_by_sections
GeminiNeuralEmbeddingGenerator = step3_module.GeminiNeuralEmbeddingGenerator
LocalVectorStoreHNSW = step4_module.LocalVectorStoreHNSW


class DenseRetriever:
    """
    Handles query embedding generation and Top-K vector search against ChromaDB.
    """
    def __init__(self, vector_store: LocalVectorStoreHNSW, embedder: GeminiNeuralEmbeddingGenerator):
        self.vector_store = vector_store
        self.embedder = embedder

    def retrieve(self, user_query: str, top_k: int = 2, score_threshold: float = 0.10, filter_metadata: dict = None) -> list[dict]:
        """
        Converts query to vector, searches HNSW store, and returns Top-K matched chunks.
        """
        print(f"\n[STEP 5 - RETRIEVAL] Searching for Query: '{user_query}'...")
        
        # 1. QUERY EMBEDDING: Convert query string to neural vector
        query_vector = self.embedder.embed_query(user_query)
        
        # 2. VECTOR DB SEARCH: Query Vector Store with Top-K and optional metadata filter
        results = self.vector_store.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=filter_metadata
        )
        
        # Parse ChromaDB query response
        retrieved_chunks = []
        if results and results["documents"] and len(results["documents"][0]) > 0:
            doc_texts = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            chunk_ids = results["ids"][0]
            
            for idx in range(len(doc_texts)):
                distance = distances[idx]
                similarity_score = float(1.0 - distance)
                
                if similarity_score >= score_threshold:
                    retrieved_chunks.append({
                        "chunk_id": chunk_ids[idx],
                        "similarity_score": similarity_score,
                        "source_file": metadatas[idx].get("source_file", ""),
                        "recipe_id": metadatas[idx].get("recipe_id", ""),
                        "cuisine": metadatas[idx].get("cuisine", ""),
                        "dietary_tags": metadatas[idx].get("dietary_tags", ""),
                        "section_title": metadatas[idx].get("section_title", ""),
                        "content": doc_texts[idx]
                    })
                    
        return retrieved_chunks


if __name__ == "__main__":
    print("=== STEP 5: DENSE RETRIEVAL & SIMILARITY SEARCH TEST ===\n")
    
    docs = load_markdown_documents(DOCS_DIR)
    
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document_by_sections(doc))
        
    BGETextEmbeddingGenerator = getattr(step3_module, "BGETextEmbeddingGenerator", step3_module.GeminiNeuralEmbeddingGenerator)
    embedder = BGETextEmbeddingGenerator(model_name="BAAI/bge-small-en-v1.5")
    embedded_chunks = embedder.generate_embeddings(all_chunks)
    
    vector_db = LocalVectorStoreHNSW(collection_name="developer_docs_hnsw")
    vector_db.add_chunks(embedded_chunks)
    print(f"Vector Store Status: {vector_db.count()} indexed vector(s) stored.")
    
    retriever = DenseRetriever(vector_store=vector_db, embedder=embedder)
    
    # TEST 1: Rate Limit Query
    q1 = "What is the maximum request rate limit for standard tier API keys?"
    matches_q1 = retriever.retrieve(user_query=q1, top_k=2, score_threshold=0.10)
    
    print(f"\nTop-{len(matches_q1)} Match(es) for Rate Limit Query:")
    print("=" * 65)
    if matches_q1:
        for m in matches_q1:
            print(f"📌 Similarity Score: {m['similarity_score']:.4f} | Chunk ID: [{m['chunk_id']}]")
            print(f"   Section: '{m['section_title']}' (Source: {m['source_file']})")
            print(f"   Snippet: \"{m['content'][:120]}...\"\n")
    print("=" * 65)
    
    # TEST 2: Webhook Security Query
    q2 = "How do I verify HMAC signatures for incoming webhooks?"
    matches_q2 = retriever.retrieve(user_query=q2, top_k=2, score_threshold=0.10)
    
    print(f"\nTop-{len(matches_q2)} Match(es) for Webhook Query:")
    print("=" * 65)
    if matches_q2:
        for m in matches_q2:
            print(f"📌 Similarity Score: {m['similarity_score']:.4f} | Chunk ID: [{m['chunk_id']}]")
            print(f"   Section: '{m['section_title']}' (Source: {m['source_file']})")
            print(f"   Snippet: \"{m['content'][:120]}...\"\n")
    print("=" * 65)
