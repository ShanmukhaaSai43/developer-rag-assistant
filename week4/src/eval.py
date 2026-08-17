"""
===================================================================
WEEK 4: Golden Set Benchmark & Failure Diagnostic Suite
===================================================================
Runs evaluation across the 12-question Golden Set:
1. Baseline Dense Retriever
2. Upgraded Hybrid BM25 + RRF (k=60) Retriever
3. Measures Hit-Rate@3, MRR@3, and p50 Latency
4. Categorizes failures into R (Retrieval), G (Generation), Not-In-Corpus
"""

import json
import time
import statistics
from pathlib import Path
from week4.src.retrievers import (
    DenseVectorRetriever,
    BM25Retriever,
    HybridRRFRetriever,
    CrossEncoderReranker,
    MMRRetriever,
    generate_grounded_answer
)

WEEK4_DIR = Path(__file__).parent.parent
GOLDEN_SET_PATH = WEEK4_DIR / "golden_set.jsonl"
CORPUS_CACHE_PATH = WEEK4_DIR / "corpus_chunks.json"


def load_golden_set() -> list[dict]:
    queries = []
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line.strip()))
    return queries


def load_corpus() -> list[dict]:
    with open(CORPUS_CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_retriever(retriever_func, golden_set: list[dict], mode_name: str = "Dense Baseline") -> dict:
    """
    Evaluates a retriever function against golden_set.
    Computes Hit-Rate@3, MRR@3, latency distribution (p50, p95), and failure details.
    """
    results = []
    hits = 0
    reciprocal_ranks = []
    latencies_ms = []

    for item in golden_set:
        qid = item["id"]
        query = item["query"]
        expected_cid = item["expected_chunk_id"]

        t0 = time.perf_counter()
        top_chunks = retriever_func(query, top_k=3)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)

        retrieved_ids = [c["chunk_id"] for c in top_chunks]
        hit = expected_cid in retrieved_ids
        rank = (retrieved_ids.index(expected_cid) + 1) if hit else 0

        if hit:
            hits += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

        # Diagnose failure type
        failure_type = "PASS"
        evidence = "Correct chunk present in Top-3."

        if not hit:
            # Check if expected chunk exists in the entire corpus
            corpus_all_ids = [c["chunk_id"] for c in load_corpus()]
            if expected_cid not in corpus_all_ids:
                failure_type = "Not-In-Corpus"
                evidence = f"Expected chunk '{expected_cid}' does not exist in ingested corpus."
            else:
                failure_type = "R"
                top_retrieved_str = ", ".join(retrieved_ids) if retrieved_ids else "None"
                evidence = f"Retriever returned [{top_retrieved_str}] missing target '{expected_cid}'."

        results.append({
            "id": qid,
            "query": query,
            "query_type": item.get("query_type", "general"),
            "expected_chunk_id": expected_cid,
            "retrieved_chunk_ids": retrieved_ids,
            "hit": hit,
            "rank": rank,
            "failure_type": failure_type,
            "evidence": evidence,
            "latency_ms": round(elapsed_ms, 2)
        })

    hit_rate = hits / len(golden_set) if golden_set else 0.0
    mrr = statistics.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    p50_latency = statistics.median(latencies_ms) if latencies_ms else 0.0
    p95_latency = statistics.quantiles(latencies_ms, n=20)[18] if len(latencies_ms) >= 20 else max(latencies_ms)

    return {
        "mode": mode_name,
        "total_queries": len(golden_set),
        "hits_at_3": hits,
        "hit_rate_at_3": round(hit_rate, 4),
        "mrr_at_3": round(mrr, 4),
        "p50_latency_ms": round(p50_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "query_results": results
    }


def run_full_comparison():
    """Runs baseline dense vs hybrid evaluation and outputs the comparison summary."""
    corpus = load_corpus()
    golden_set = load_golden_set()

    dense_retriever = DenseVectorRetriever()
    bm25_retriever = BM25Retriever(corpus)
    hybrid_retriever = HybridRRFRetriever(dense_retriever, bm25_retriever, k=60)

    # 1. Baseline Evaluation
    baseline_eval = evaluate_retriever(
        lambda q, top_k: dense_retriever.search(q, top_k=top_k),
        golden_set,
        mode_name="Baseline Dense (Vector)"
    )

    # 2. Hybrid (BM25 + RRF) Evaluation
    hybrid_eval = evaluate_retriever(
        lambda q, top_k: hybrid_retriever.search(q, top_k=top_k)["top_chunks"],
        golden_set,
        mode_name="Hybrid Search (BM25 + RRF k=60)"
    )

    return {
        "baseline": baseline_eval,
        "hybrid": hybrid_eval
    }


if __name__ == "__main__":
    res = run_full_comparison()
    print("\n" + "=" * 65)
    print("WEEK 4 BENCHMARK: BASELINE vs. HYBRID (RRF k=60)")
    print("=" * 65)
    print(f"Baseline Dense Hit-Rate@3: {res['baseline']['hit_rate_at_3']*100:.1f}% | p50 Latency: {res['baseline']['p50_latency_ms']} ms")
    print(f"Hybrid RRF Hit-Rate@3:     {res['hybrid']['hit_rate_at_3']*100:.1f}% | p50 Latency: {res['hybrid']['p50_latency_ms']} ms")
    print("=" * 65)
