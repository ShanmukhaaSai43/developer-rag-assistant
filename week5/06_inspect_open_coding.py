"""
===================================================================
Inspect all 20 sampled traces in detail for open-coding
===================================================================
"""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

data_file = Path(__file__).parent / "sampled_20_traces.json"
with open(data_file, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Loaded {len(data['traces'])} sampled traces (Seed: {data['seed']}):\n")
for t in data["traces"]:
    print(f"================================================================================")
    print(f"[{t['index']:02d}/20] TRACE ID: {t['trace_id']}")
    print(f"QUERY:           {t['user_query']}")
    print(f"RETRIEVED CHUNKS:")
    for c in t["retrieved_chunks"]:
        print(f"  - [{c['chunk_id']}] (Score: {c['similarity_score']}) File: {c['source_file']}")
    print(f"RAW OUTPUT:")
    print(t["raw_output"])
    print()
