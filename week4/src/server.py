"""
===================================================================
WEEK 4: FastAPI Server & Inspection API
===================================================================
Provides real-time endpoints for the interactive React UI:
- /api/corpus: List of all 9 recipes and their chunks
- /api/search: Multi-mode retrieval search (Dense, BM25, Hybrid, Rerank, MMR)
- /api/chat: Grounded Q&A response with citation bounds
- /api/eval: Golden Set benchmark runner (Baseline vs. Hybrid)
- /api/golden-set: Golden set questions and known correct chunk IDs
"""

import os
import json
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from week4.src.retrievers import (
    DenseVectorRetriever,
    BM25Retriever,
    HybridRRFRetriever,
    CrossEncoderReranker,
    MMRRetriever,
    generate_grounded_answer
)
from week4.src.eval import load_golden_set, evaluate_retriever

WEEK4_DIR = Path(__file__).parent.parent
STATIC_DIR = WEEK4_DIR / "static"
CORPUS_CACHE_PATH = WEEK4_DIR / "corpus_chunks.json"

# Ingest corpus if not cached
if not CORPUS_CACHE_PATH.exists():
    from week4.src.ingest import build_and_save_index
    build_and_save_index()

with open(CORPUS_CACHE_PATH, "r", encoding="utf-8") as f:
    corpus_chunks = json.load(f)

# Initialize Retrievers
dense_retriever = DenseVectorRetriever()
bm25_retriever = BM25Retriever(corpus_chunks)
hybrid_retriever = HybridRRFRetriever(dense_retriever, bm25_retriever, k=60)
reranker = CrossEncoderReranker(dense_retriever)
mmr_retriever = MMRRetriever(dense_retriever)

app = FastAPI(title="Week 4 Recipe Assistant & Retrieval Debugger")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str
    mode: str = "hybrid" # dense, bm25, hybrid, rerank, mmr
    top_k: int = 3
    mmr_lambda: float = 0.7


class ChatRequest(BaseModel):
    query: str
    mode: str = "hybrid"
    top_k: int = 3


@app.get("/api/corpus")
def get_corpus():
    return {
        "total_chunks": len(corpus_chunks),
        "chunks": corpus_chunks
    }


@app.get("/api/golden-set")
def get_golden_set_api():
    return load_golden_set()


@app.get("/api/inspection")
def get_inspection_api():
    """Dynamically evaluates baseline dense retrieval and diagnoses failures with live evidence."""
    golden_set = load_golden_set()
    all_corpus_ids = set(c["chunk_id"] for c in corpus_chunks)
    corpus_map = {c["chunk_id"]: c for c in corpus_chunks}
    
    tally = {"R": 0, "G": 0, "Not-In-Corpus": 0, "PASS": 0}
    diagnosed = []
    
    for item in golden_set:
        qid = item["id"]
        query = item["query"]
        expected_cid = item["expected_chunk_id"]
        target_entity = item.get("target_entity", "")
        
        # Real-time Dense Query
        dense_results = dense_retriever.search(query, top_k=3)
        retrieved_ids = [c["chunk_id"] for c in dense_results]
        is_hit = expected_cid in retrieved_ids
        rank = (retrieved_ids.index(expected_cid) + 1) if is_hit else 0
        
        if is_hit:
            label = "PASS"
            tally["PASS"] += 1
            evidence = f"Target chunk '{expected_cid}' found at Rank #{rank} (Sim: {dense_results[rank-1].get('dense_score', 0):.4f})."
        else:
            if expected_cid not in all_corpus_ids:
                label = "Not-In-Corpus"
                tally["Not-In-Corpus"] += 1
                evidence = f"Expected chunk '{expected_cid}' does not exist anywhere in the corpus."
            else:
                label = "R"
                tally["R"] += 1
                top1_title = dense_results[0].get("section_title", "Unknown") if dense_results else "None"
                evidence = f"Dense search fetched [{', '.join(retrieved_ids)}] (Top-1: '{top1_title}'), missing target '{expected_cid}'."
                
        diagnosed.append({
            "id": qid,
            "query": query,
            "query_type": item.get("query_type", "general"),
            "expected_chunk_id": expected_cid,
            "target_entity": target_entity,
            "retrieved_chunk_ids": retrieved_ids,
            "is_hit": is_hit,
            "rank": rank,
            "label": label,
            "evidence": evidence,
            "retrieved_chunks": dense_results
        })
        
    return {
        "tally": tally,
        "queries": diagnosed
    }


@app.post("/api/search")
def search_api(req: SearchRequest):
    t0 = time.perf_counter()
    mode = req.mode.lower()
    
    dense_candidates = dense_retriever.search(req.query, top_k=5)
    bm25_candidates = bm25_retriever.search(req.query, top_k=5)
    
    if mode == "dense":
        top_chunks = dense_candidates[:req.top_k]
    elif mode == "bm25":
        top_chunks = bm25_candidates[:req.top_k]
    elif mode == "hybrid":
        fused = hybrid_retriever.search(req.query, top_k=req.top_k)
        top_chunks = fused["top_chunks"]
    elif mode == "rerank":
        top_chunks = reranker.rerank(req.query, top_k=req.top_k)
    elif mode == "mmr":
        top_chunks = mmr_retriever.search(req.query, top_k=req.top_k, mmr_lambda=req.mmr_lambda)
    else:
        top_chunks = dense_candidates[:req.top_k]
        
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    
    return {
        "query": req.query,
        "mode": req.mode,
        "elapsed_ms": round(elapsed_ms, 2),
        "top_chunks": top_chunks,
        "dense_candidates": dense_candidates,
        "bm25_candidates": bm25_candidates
    }


@app.post("/api/chat")
def chat_api(req: ChatRequest):
    t0 = time.perf_counter()
    search_res = search_api(SearchRequest(query=req.query, mode=req.mode, top_k=req.top_k))
    top_chunks = search_res["top_chunks"]
    
    grounded_res = generate_grounded_answer(req.query, top_chunks)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    
    return {
        "query": req.query,
        "mode": req.mode,
        "answer": grounded_res["answer"],
        "citations": grounded_res["citations"],
        "grounded": grounded_res["grounded"],
        "top_chunks": top_chunks,
        "dense_candidates": search_res["dense_candidates"],
        "bm25_candidates": search_res["bm25_candidates"],
        "elapsed_ms": round(elapsed_ms, 2)
    }


@app.post("/api/eval")
def eval_api():
    golden_set = load_golden_set()
    
    baseline = evaluate_retriever(
        lambda q, top_k: dense_retriever.search(q, top_k=top_k),
        golden_set,
        mode_name="Baseline Dense (Vector)"
    )
    
    hybrid = evaluate_retriever(
        lambda q, top_k: hybrid_retriever.search(q, top_k=top_k)["top_chunks"],
        golden_set,
        mode_name="Hybrid Search (BM25 + RRF k=60)"
    )
    
    rerank = evaluate_retriever(
        lambda q, top_k: reranker.rerank(q, top_k=top_k),
        golden_set,
        mode_name="Cross-Encoder Reranker"
    )
    
    # Calculate fixed / unfixed per-query breakdown between baseline and hybrid
    comparison_table = []
    for b_item, h_item in zip(baseline["query_results"], hybrid["query_results"]):
        b_hit = b_item["hit"]
        h_hit = h_item["hit"]
        
        status = "PASSED_BOTH"
        if not b_hit and h_hit:
            status = "FIXED_BY_HYBRID"
        elif not b_hit and not h_hit:
            status = "UNTOUCHED_FAIL"
        elif b_hit and not h_hit:
            status = "REGRESSION"
            
        comparison_table.append({
            "id": b_item["id"],
            "query": b_item["query"],
            "query_type": b_item["query_type"],
            "expected_chunk_id": b_item["expected_chunk_id"],
            "baseline_hit": b_hit,
            "baseline_rank": b_item["rank"],
            "baseline_failure": b_item["failure_type"],
            "hybrid_hit": h_hit,
            "hybrid_rank": h_item["rank"],
            "status": status,
            "evidence": b_item["evidence"]
        })
        
    return {
        "baseline": baseline,
        "hybrid": hybrid,
        "rerank": rerank,
        "comparison_table": comparison_table
    }


# Mount UI static directory
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
