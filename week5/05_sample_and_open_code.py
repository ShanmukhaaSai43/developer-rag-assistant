"""
===================================================================
WEEK 5: Step 2 — Seeded Random Sampling of 20 Production Traces
===================================================================
Applies a documented random seed (seed=42) to select exactly 20 traces
from the production trace pool for hand open-coding.
===================================================================
"""

import os
import sys
import json
import random
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from week5.trace_system import CompleteTracer

SAMPLE_SEED = 42
SAMPLE_SIZE = 20

def main():
    tracer = CompleteTracer()
    traces = tracer.load_all_traces()

    # Deduplicate traces by trace_id or user_query
    seen_queries = set()
    unique_traces = []
    for t in traces:
        if t["user_query"] not in seen_queries:
            seen_queries.add(t["user_query"])
            unique_traces.append(t)

    print(f"Total Unique Traces in Pool: {len(unique_traces)}")

    random.seed(SAMPLE_SEED)
    sampled_traces = random.sample(unique_traces, k=min(SAMPLE_SIZE, len(unique_traces)))

    print("\n" + "=" * 80)
    print(f"SEEDED RANDOM SAMPLE OF {len(sampled_traces)} TRACES (Seed: {SAMPLE_SEED})")
    print("=" * 80)

    sample_summary = []
    for idx, t in enumerate(sampled_traces, 1):
        print(f"\n[{idx:02d}/20] Trace ID: {t['trace_id']}")
        print(f"       User Query:       \"{t['user_query']}\"")
        retrieved_summary = [f"{c['chunk_id']} ({c['similarity_score']})" for c in t['retrieved_chunks']]
        print(f"       Retrieved Chunks: {', '.join(retrieved_summary) if retrieved_summary else '[NONE]'}")
        print(f"       Raw Output:       \"{t['raw_output'][:150]}...\"" if len(t['raw_output']) > 150 else f"       Raw Output:       \"{t['raw_output']}\"")
        
        sample_summary.append({
            "index": idx,
            "trace_id": t["trace_id"],
            "user_query": t["user_query"],
            "retrieved_chunks": t["retrieved_chunks"],
            "raw_output": t["raw_output"]
        })

    # Save sampled list
    sample_file = Path(__file__).parent / "sampled_20_traces.json"
    with open(sample_file, "w", encoding="utf-8") as f:
        json.dump({
            "seed": SAMPLE_SEED,
            "sample_size": len(sampled_traces),
            "traces": sample_summary
        }, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"Sampled traces saved to: {sample_file}")
    print("Seeded Trace IDs:")
    print([t["trace_id"] for t in sampled_traces])

if __name__ == "__main__":
    main()
