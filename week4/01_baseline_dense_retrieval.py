"""
===================================================================
WEEK 4 · TASK 1: Baseline Dense Vector Retrieval & Evaluation
===================================================================
GOAL:
1. Ingest the 6 official recipe markdown cards from week4/docs/
2. Split them into Structure-Aware Section Chunks (Overview, Ingredients, Method, Allergen)
3. Embed chunks into ChromaDB using local FastEmbed ('BAAI/bge-small-en-v1.5')
4. Evaluate Baseline Dense Retrieval against the 12-Question Golden Set
5. Measure and record:
   - Baseline Hit-Rate@3
   - Baseline p50 Latency (ms)
"""

import os
import re
import json
import time
import statistics
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

WEEK4_DIR = Path(__file__).parent
DOCS_DIR = WEEK4_DIR / "docs"
CHROMA_DIR = WEEK4_DIR / ".chroma_db"
GOLDEN_SET_PATH = WEEK4_DIR / "golden_set.jsonl"
CORPUS_CACHE_PATH = WEEK4_DIR / "corpus_chunks.json"
COLLECTION_NAME = "week4_recipe_corpus"


# -------------------------------------------------------------------
# 1. FRONTMATTER PARSING & SECTION CHUNKING
# -------------------------------------------------------------------
def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract metadata headers from markdown files."""
    frontmatter = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body = parts[2].strip()
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip()] = v.strip()
    return frontmatter, body


def load_and_chunk_recipes() -> list[dict]:
    """Loads all 6 recipe cards and splits them by section headers."""
    chunks = []
    recipe_files = sorted(DOCS_DIR.glob("*.md"))
    
    for file_path in recipe_files:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
        fm, clean_body = parse_frontmatter(raw_text)
        recipe_id = fm.get("recipe_id", file_path.stem)
        cuisine = fm.get("cuisine", "general")
        dietary_tags = fm.get("dietary_tags", "none")
        
        # Extract main title
        h1_match = re.search(r'^#\s+(.+)$', clean_body, re.MULTILINE)
        h1_title = h1_match.group(1).strip() if h1_match else recipe_id
        
        sections = re.split(r'\n(?=##\s+)', clean_body)
        chunk_idx = 1
        
        for section in sections:
            clean_section = section.strip()
            if not clean_section:
                continue
                
            # Skip standalone title chunk
            if clean_section.startswith("# ") and "##" not in clean_section and len(clean_section.splitlines()) <= 2:
                continue
                
            first_line = clean_section.split("\n")[0].replace("#", "").strip()
            chunk_content = clean_section if clean_section.startswith("# ") else f"[{h1_title}] {clean_section}"
            
            chunk_obj = {
                "chunk_id": f"{recipe_id}#section_{chunk_idx}",
                "source_file": file_path.name,
                "recipe_id": recipe_id,
                "recipe_name": h1_title,
                "cuisine": cuisine,
                "dietary_tags": dietary_tags,
                "section_title": first_line,
                "char_count": len(chunk_content),
                "content": chunk_content
            }
            chunks.append(chunk_obj)
            chunk_idx += 1
            
    return chunks


# -------------------------------------------------------------------
# 2. CHROMADB VECTOR INDEXING
# -------------------------------------------------------------------
def build_vector_store(chunks: list[dict]):
    """Embeds chunks with FastEmbed and stores vectors in persistent ChromaDB."""
    import chromadb
    from fastembed import TextEmbedding
    
    # Save JSON cache for inspection
    with open(CORPUS_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
        
    embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    texts = [c["content"] for c in chunks]
    embeddings = [list(map(float, vec)) for vec in embedder.embed(texts)]
    
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
        
    collection = client.create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    
    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings,
        metadatas=[{
            "chunk_id": c["chunk_id"],
            "source_file": c["source_file"],
            "recipe_id": c["recipe_id"],
            "cuisine": c["cuisine"],
            "dietary_tags": c["dietary_tags"],
            "section_title": c["section_title"]
        } for c in chunks],
        documents=texts
    )
    return client, collection, embedder


# -------------------------------------------------------------------
# 3. BASELINE DENSE RETRIEVAL EVALUATION
# -------------------------------------------------------------------
def run_baseline_evaluation():
    print("=" * 75)
    print("STEP 1: INGESTING 6 RECIPES & CREATING SECTION CHUNKS")
    print("=" * 75)
    
    chunks = load_and_chunk_recipes()
    print(f"Loaded {len(chunks)} section chunks across 6 recipe documents.")
    for c in chunks[:4]:
        print(f"  [{c['chunk_id']}] -> {c['section_title']} ({c['recipe_name']})")
        
    print("\nBuilding Dense Vector Store (BAAI/bge-small-en-v1.5)...")
    client, collection, embedder = build_vector_store(chunks)
    print(f"ChromaDB Collection '{COLLECTION_NAME}' indexed with {collection.count()} chunks.")
    
    print("\n" + "=" * 75)
    print("STEP 2: RUNNING BASELINE DENSE EVALUATION ON 12-QUESTION GOLDEN SET")
    print("=" * 75)
    
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        golden_set = [json.loads(line.strip()) for line in f if line.strip()]
        
    hits = 0
    latencies_ms = []
    
    print(f"{'ID':<5} | {'Type':<12} | {'Expected Chunk':<28} | {'Top-3 Retrieved':<30} | {'Hit?':<5} | {'p50 (ms)'}")
    print("-" * 105)
    
    for item in golden_set:
        qid = item["id"]
        qtype = item["query_type"]
        query = item["query"]
        expected_cid = item["expected_chunk_id"]
        
        t0 = time.perf_counter()
        query_vec = [list(map(float, vec)) for vec in embedder.embed([query])][0]
        res = collection.query(
            query_embeddings=[query_vec],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)
        
        retrieved_ids = res["ids"][0] if res and res["ids"] else []
        is_hit = expected_cid in retrieved_ids
        if is_hit:
            hits += 1
            hit_str = "[HIT]"
        else:
            hit_str = "[MISS]"
            
        retrieved_str = ", ".join(retrieved_ids)
        print(f"{qid:<5} | {qtype:<12} | {expected_cid:<28} | {retrieved_str:<30} | {hit_str:<6} | {elapsed_ms:.2f} ms")
        
    hit_rate = (hits / len(golden_set)) * 100.0
    p50_lat = statistics.median(latencies_ms)
    
    print("=" * 105)
    print("TASK 1 BASELINE RESULTS:")
    print(f"   * Total Questions Evaluated: {len(golden_set)}")
    print(f"   * Baseline Hits @ 3:         {hits} / {len(golden_set)}")
    print(f"   * Baseline Hit-Rate @ 3:     {hit_rate:.1f}%")
    print(f"   * Baseline p50 Latency:      {p50_lat:.2f} ms")
    print("=" * 105)


if __name__ == "__main__":
    run_baseline_evaluation()
