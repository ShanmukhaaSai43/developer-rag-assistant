"""
===================================================================
WEEK 4 · TASK 4: MMR Diversity & Cross-Encoder Reranking Lab
===================================================================
GOAL:
1. Implement Maximal Marginal Relevance (MMR) to solve context redundancy in Top-k.
2. Implement Cross-Encoder full query-document attention reranking.
3. Compare MMR λ=1.0 (pure relevance / redundancy) vs. λ=0.5 (balanced diversity).
4. Measure Intra-List Similarity (redundancy metric) and latency impact.
"""

import json
import time
import numpy as np
from pathlib import Path
import chromadb
from fastembed import TextEmbedding

WEEK4_DIR = Path(__file__).parent
CHROMA_DIR = WEEK4_DIR / ".chroma_db"
CORPUS_CACHE_PATH = WEEK4_DIR / "corpus_chunks.json"
COLLECTION_NAME = "week4_recipe_corpus"


# ===================================================================
# 1. MMR (MAXIMAL MARGINAL RELEVANCE) RETRIEVER
# ===================================================================
class MMRRetriever:
    """
    MMR Algorithm:
    ArgMax_{d in C \ S} [ lambda * Sim(d, query) - (1 - lambda) * Max_{s in S} Sim(d, s) ]
    
    - lambda = 1.0: Pure Relevance (often returns duplicate/near-identical chunks)
    - lambda = 0.5: Balanced Relevance & Diversity (ensures varied recipe sections)
    """
    def __init__(self, collection, embedder):
        self.collection = collection
        self.embedder = embedder

    @staticmethod
    def _cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def search(self, query: str, top_k: int = 3, mmr_lambda: float = 0.5, candidate_pool: int = 12) -> list[dict]:
        query_vec = np.array(list(self.embedder.embed([query]))[0], dtype=np.float32)
        
        # 1. Fetch top candidate pool from ChromaDB
        res = self.collection.query(
            query_embeddings=[query_vec.tolist()],
            n_results=candidate_pool,
            include=["documents", "metadatas", "distances"]
        )

        if not res or not res["ids"] or not res["ids"][0]:
            return []

        cand_ids = res["ids"][0]
        cand_docs = res["documents"][0]
        cand_metas = res["metadatas"][0]
        cand_dists = res["distances"][0]

        # Embed all candidate texts for pairwise diversity calculation
        cand_embeds = [np.array(e, dtype=np.float32) for e in self.embedder.embed(cand_docs)]

        # Precompute query-document similarities
        query_sims = [max(0.0, 1.0 - dist) for dist in cand_dists]

        selected_indices = []
        unselected_indices = list(range(len(cand_ids)))

        # Iteratively select top_k items maximizing MMR objective
        for _ in range(min(top_k, len(cand_ids))):
            best_idx = None
            best_mmr_score = -float("inf")

            for idx in unselected_indices:
                rel_score = query_sims[idx]

                # Max similarity to already selected chunks
                if not selected_indices:
                    max_sim_to_selected = 0.0
                else:
                    max_sim_to_selected = max(
                        self._cosine_similarity(cand_embeds[idx], cand_embeds[s_idx])
                        for s_idx in selected_indices
                    )

                mmr_score = (mmr_lambda * rel_score) - ((1.0 - mmr_lambda) * max_sim_to_selected)

                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_idx = idx

            if best_idx is not None:
                selected_indices.append(best_idx)
                unselected_indices.remove(best_idx)

        # Build formatted output
        results = []
        for rank, idx in enumerate(selected_indices, 1):
            item = dict(cand_metas[idx])
            item["chunk_id"] = cand_ids[idx]
            item["content"] = cand_docs[idx]
            item["relevance_score"] = round(query_sims[idx], 4)
            item["mmr_rank"] = rank
            results.append(item)

        return results


# ===================================================================
# 2. INTRA-LIST SIMILARITY (REDUNDANCY METRIC)
# ===================================================================
def compute_intra_list_similarity(chunks: list[dict], embedder) -> float:
    """Measures the average pairwise similarity between retrieved chunks (lower = more diverse)."""
    if len(chunks) < 2:
        return 0.0
    
    texts = [c["content"] for c in chunks]
    embeds = [np.array(e, dtype=np.float32) for e in embedder.embed(texts)]
    
    sims = []
    for i in range(len(embeds)):
        for j in range(i + 1, len(embeds)):
            norm_i = np.linalg.norm(embeds[i])
            norm_j = np.linalg.norm(embeds[j])
            sim = float(np.dot(embeds[i], embeds[j]) / (norm_i * norm_j))
            sims.append(sim)
            
    return float(np.mean(sims)) if sims else 0.0


# ===================================================================
# 3. DEMONSTRATION OF MMR DIVERSITY ON COMPLEX RECIPE QUERY
# ===================================================================
def run_mmr_diversity_demo():
    print("=" * 85)
    print("TASK 4: MMR DIVERSITY & CONTEXT REDUNDANCY REDUCTION LAB")
    print("=" * 85)

    with open(CORPUS_CACHE_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)
    embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    mmr = MMRRetriever(collection, embedder)

    test_query = "Give me complete instructions to make Country Sourdough Bread from scratch"
    print(f"\nExploratory Query: \"{test_query}\"\n")

    # 1. Test Standard Pure Relevance (λ = 1.0)
    # 1. Test Standard Pure Relevance (lambda = 1.0)
    t0 = time.perf_counter()
    chunks_lambda_1 = mmr.search(test_query, top_k=3, mmr_lambda=1.0)
    t_lambda_1 = (time.perf_counter() - t0) * 1000.0
    redundancy_1 = compute_intra_list_similarity(chunks_lambda_1, embedder)

    print("-------------------------------------------------------------------------------------")
    print("TEST A: STANDARD RETRIEVAL / MMR lambda = 1.0 (PURE RELEVANCE - HIGHER REDUNDANCY)")
    print("-------------------------------------------------------------------------------------")
    for c in chunks_lambda_1:
        print(f"  #{c['mmr_rank']} [{c['chunk_id']}] {c['section_title']} (Relevance: {c['relevance_score']})")
        print(f"     Preview: {c['content'][:90].replace(chr(10), ' ')}...")
    print(f"  * Intra-List Redundancy (Pairwise Sim): {redundancy_1:.4f} (Higher redundancy)")
    print(f"  * Latency: {t_lambda_1:.2f} ms")

    # 2. Test Balanced MMR Diversity (lambda = 0.5)
    t0 = time.perf_counter()
    chunks_lambda_05 = mmr.search(test_query, top_k=3, mmr_lambda=0.5)
    t_lambda_05 = (time.perf_counter() - t0) * 1000.0
    redundancy_05 = compute_intra_list_similarity(chunks_lambda_05, embedder)

    print("\n-------------------------------------------------------------------------------------")
    print("TEST B: BALANCED MMR lambda = 0.5 (RELEVANCE + DIVERSITY - MULTI-SECTION COVERAGE)")
    print("-------------------------------------------------------------------------------------")
    for c in chunks_lambda_05:
        print(f"  #{c['mmr_rank']} [{c['chunk_id']}] {c['section_title']} (Relevance: {c['relevance_score']})")
        print(f"     Preview: {c['content'][:90].replace(chr(10), ' ')}...")
    print(f"  * Intra-List Redundancy (Pairwise Sim): {redundancy_05:.4f} (Reduced redundancy!)")
    print(f"  * Latency: {t_lambda_05:.2f} ms")

    # Comparison summary
    print("\n" + "=" * 85)
    print("TASK 4 SUMMARY & ARCHITECTURAL TAKEAWAYS:")
    print("=" * 85)
    print("1. Problem in Standard Dense (lambda=1.0):")
    print("   Standard dense search often pulls overlapping paragraphs from the exact same section,")
    print("   wasting LLM context tokens with repetitive sentences.")
    print("\n2. MMR Fix (lambda=0.5):")
    print("   MMR penalizes chunks that are too similar to already-selected chunks, forcing the context")
    print("   window to include diverse recipe sections (e.g. Overview + Ingredients + Method steps).")
    print(f"\n3. Quantitative Proof:")
    print(f"   Intra-List Redundancy reduced from {redundancy_1:.4f} down to {redundancy_05:.4f}.")
    print("=" * 85)


if __name__ == "__main__":
    run_mmr_diversity_demo()
