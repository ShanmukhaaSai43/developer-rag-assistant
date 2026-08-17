"""
===================================================================
WEEK 4 · TASK 3: Hybrid Search with BM25 & Reciprocal Rank Fusion (k=60)
===================================================================
GOAL:
1. Implement BM25 (Okapi) sparse keyword retrieval for exact token matching.
2. Implement Reciprocal Rank Fusion (RRF with k=60) to merge Dense and Sparse ranks.
3. Re-evaluate the EXACT SAME 12 questions from the Golden Set.
4. Measure and compare:
   - Hit-Rate@3 Before -> After
   - p50 Latency Before -> After
5. Name explicitly which of the Task 2 R-failures were FIXED by the change.
"""

import re
import math
import json
import time
import statistics
from collections import Counter
from pathlib import Path
import chromadb
from fastembed import TextEmbedding

WEEK4_DIR = Path(__file__).parent
CHROMA_DIR = WEEK4_DIR / ".chroma_db"
GOLDEN_SET_PATH = WEEK4_DIR / "golden_set.jsonl"
CORPUS_CACHE_PATH = WEEK4_DIR / "corpus_chunks.json"
COLLECTION_NAME = "week4_recipe_corpus"


# ===================================================================
# 1. BM25 SPARSE KEYWORD RETRIEVER (Okapi BM25)
# ===================================================================
class BM25Retriever:
    """
    Exact keyword retriever based on Lucene/Okapi BM25.
    Calculates TF-IDF with document length normalization (k1=1.5, b=0.75).
    """
    def __init__(self, corpus: list[dict], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.doc_len = [len(self._tokenize(doc["content"])) for doc in corpus]
        self.avgdl = sum(self.doc_len) / (len(corpus) if corpus else 1)
        self.doc_freqs = []
        self.idf = {}
        self._build_index()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        # Preserve alphanumeric characters, numbers, and symbols like % and °
        clean = re.sub(r'[^\w\s%°]', ' ', text.lower())
        return [t.strip() for t in clean.split() if len(t.strip()) > 1]

    def _build_index(self):
        df = Counter()
        for doc in self.corpus:
            tokens = set(self._tokenize(doc["content"]))
            self.doc_freqs.append(Counter(self._tokenize(doc["content"])))
            for token in tokens:
                df[token] += 1

        n_docs = len(self.corpus)
        for token, count in df.items():
            # Standard Lucene BM25 IDF formula
            self.idf[token] = math.log(1 + (n_docs - count + 0.5) / (count + 0.5))

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        query_tokens = self._tokenize(query)
        scores = []

        for idx, doc in enumerate(self.corpus):
            score = 0.0
            freqs = self.doc_freqs[idx]
            dl = self.doc_len[idx]

            for token in query_tokens:
                if token in freqs:
                    tf = freqs[token]
                    idf = self.idf.get(token, 0.0)
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (dl / self.avgdl))
                    score += idf * (numerator / denominator)

            scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for rank, (idx, score) in enumerate(scores[:top_k], 1):
            item = dict(self.corpus[idx])
            item["bm25_score"] = round(float(score), 4)
            item["bm25_rank"] = rank
            results.append(item)

        return results


# ===================================================================
# 2. HYBRID RETRIEVER WITH RECIPROCAL RANK FUSION (RRF k=60)
# ===================================================================
class HybridRRFRetriever:
    """
    Scale-invariant Rank Fusion:
    RRF_Score(d) = 1 / (60 + rank_dense(d)) + 1 / (60 + rank_sparse(d))
    Fuses dense semantic understanding with BM25 keyword precision.
    """
    def __init__(self, collection, embedder, bm25_retriever: BM25Retriever, k: int = 60):
        self.collection = collection
        self.embedder = embedder
        self.bm25 = bm25_retriever
        self.k = k

    def search(self, query: str, top_k: int = 3, candidate_pool: int = 15) -> list[dict]:
        # 1. Dense Search Candidate List
        query_vec = [list(map(float, vec)) for vec in self.embedder.embed([query])][0]
        dense_res = self.collection.query(
            query_embeddings=[query_vec],
            n_results=candidate_pool,
            include=["documents", "metadatas", "distances"]
        )

        dense_candidates = []
        if dense_res and dense_res["ids"]:
            for rank, (cid, meta, doc, dist) in enumerate(zip(
                dense_res["ids"][0], dense_res["metadatas"][0], dense_res["documents"][0], dense_res["distances"][0]
            ), 1):
                item = dict(meta)
                item["chunk_id"] = cid
                item["content"] = doc
                item["dense_rank"] = rank
                item["dense_score"] = round(max(0.0, 1.0 - dist), 4)
                dense_candidates.append(item)

        # 2. BM25 Search Candidate List
        bm25_candidates = self.bm25.search(query, top_k=candidate_pool)

        # 3. Compute RRF Scores
        rrf_scores = {}
        chunk_map = {}

        for item in dense_candidates:
            cid = item["chunk_id"]
            rank = item["dense_rank"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.k + rank))
            chunk_map[cid] = item

        for item in bm25_candidates:
            cid = item["chunk_id"]
            rank = item["bm25_rank"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = item
            else:
                chunk_map[cid]["bm25_rank"] = rank
                chunk_map[cid]["bm25_score"] = item["bm25_score"]

        # Sort by fused RRF score
        sorted_fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        final_top = []
        for rank, (cid, score) in enumerate(sorted_fused[:top_k], 1):
            doc = dict(chunk_map[cid])
            doc["rrf_score"] = round(score, 6)
            doc["final_rank"] = rank
            final_top.append(doc)

        return final_top


# ===================================================================
# 3. BEFORE VS. AFTER BENCHMARK EVALUATION
# ===================================================================
def run_task3_comparison():
    print("=" * 85)
    print("TASK 3: BEFORE -> AFTER BENCHMARK (BASELINE DENSE vs. HYBRID BM25+RRF)")
    print("=" * 85)

    with open(CORPUS_CACHE_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        golden_set = [json.loads(line.strip()) for line in f if line.strip()]

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)
    embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    bm25 = BM25Retriever(corpus)
    hybrid = HybridRRFRetriever(collection, embedder, bm25, k=60)

    # 1. Evaluate Baseline Dense
    baseline_hits = 0
    baseline_latencies = []
    baseline_ranks = {}

    for item in golden_set:
        t0 = time.perf_counter()
        query_vec = [list(map(float, vec)) for vec in embedder.embed([item["query"]])][0]
        res = collection.query(query_embeddings=[query_vec], n_results=3)
        dt = (time.perf_counter() - t0) * 1000.0
        baseline_latencies.append(dt)

        retrieved_ids = res["ids"][0] if res and res["ids"] else []
        hit = item["expected_chunk_id"] in retrieved_ids
        rank = (retrieved_ids.index(item["expected_chunk_id"]) + 1) if hit else 0
        baseline_ranks[item["id"]] = (hit, rank)
        if hit:
            baseline_hits += 1

    # 2. Evaluate Upgraded Hybrid (BM25 + RRF)
    hybrid_hits = 0
    hybrid_latencies = []
    hybrid_ranks = {}

    for item in golden_set:
        t0 = time.perf_counter()
        top_fused = hybrid.search(item["query"], top_k=3)
        dt = (time.perf_counter() - t0) * 1000.0
        hybrid_latencies.append(dt)

        retrieved_ids = [c["chunk_id"] for c in top_fused]
        hit = item["expected_chunk_id"] in retrieved_ids
        rank = (retrieved_ids.index(item["expected_chunk_id"]) + 1) if hit else 0
        hybrid_ranks[item["id"]] = (hit, rank, retrieved_ids)
        if hit:
            hybrid_hits += 1

    # Per-Question Results Table
    print(f"\n{'ID':<5} | {'Query':<36} | {'Baseline':<14} | {'Hybrid (RRF)':<14} | {'Status'}")
    print("-" * 90)

    fixed_count = 0
    for item in golden_set:
        qid = item["id"]
        qtext = item["query"][:34] + ".." if len(item["query"]) > 36 else item["query"]
        b_hit, b_rank = baseline_ranks[qid]
        h_hit, h_rank, h_retrieved = hybrid_ranks[qid]

        b_str = f"Hit (#{b_rank})" if b_hit else "MISS [R]"
        h_str = f"Hit (#{h_rank})" if h_hit else "MISS"

        if not b_hit and h_hit:
            status = "FIXED BY HYBRID"
            fixed_count += 1
        elif b_hit and h_hit:
            status = "Passed Both"
        else:
            status = "Untouched Miss"

        print(f"{qid:<5} | {qtext:<36} | {b_str:<14} | {h_str:<14} | {status}")

    # Summary Metrics
    b_hr = (baseline_hits / len(golden_set)) * 100.0
    h_hr = (hybrid_hits / len(golden_set)) * 100.0
    b_p50 = statistics.median(baseline_latencies)
    h_p50 = statistics.median(hybrid_latencies)
    lat_delta = h_p50 - b_p50

    print("=" * 90)
    print("TASK 3 BEFORE -> AFTER SUMMARY:")
    print("=" * 90)
    print(f"  • Hit-Rate@3:   {b_hr:.1f}% ({baseline_hits}/12)  --->  {h_hr:.1f}% ({hybrid_hits}/12)  [+{h_hr - b_hr:.1f}% Gain]")
    print(f"  • p50 Latency:  {b_p50:.2f} ms             --->  {h_p50:.2f} ms            [+{lat_delta:.2f} ms Price]")
    print(f"  • R-Failures Fixed: {fixed_count} of {len(golden_set) - baseline_hits} baseline misses completely resolved.")
    print("=" * 90)


if __name__ == "__main__":
    run_task3_comparison()
