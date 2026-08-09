"""
===================================================================
STEP 2: Section-Based Chunking & Overlap
===================================================================
GOAL: Take the ingested Markdown documents from Step 1 and split them 
      into structured chunks based on Markdown Headings (##).

Key Concepts:
- Section-based Chunking keeps headings, parameter tables, and code 
  snippets together in the same chunk.
- Every chunk inherits metadata from Step 1 (source_file, section_title).
- We also include Fixed-size chunking to compare and prove accuracy gains!
"""

import re
import importlib.util
from pathlib import Path

# Dynamically import Step 1 module (handles leading digits in filename)
DOCS_DIR = Path(__file__).parent.parent / "docs"
step1_path = Path(__file__).parent / "01_ingest_docs.py"
spec = importlib.util.spec_from_file_location("step1_module", step1_path)
step1_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step1_module)
load_markdown_documents = step1_module.load_markdown_documents


def chunk_document_by_sections(doc: dict) -> list[dict]:
    """
    STRATEGY 1 (PRIMARY): Section-Based Chunking.
    Splits a Markdown document using '## ' section headings.
    """
    raw_content = doc["content"]
    source_file = doc["source_file"]
    
    # Split text whenever we encounter a Markdown H2 heading ('\n## ')
    # Using re.split with capture group keeps the heading title!
    sections = re.split(r'\n(?=##\s+)', raw_content)
    
    chunks = []
    for idx, section in enumerate(sections, 1):
        clean_section = section.strip()
        if not clean_section:
            continue
            
        # Extract the first line as the Section Header Title
        first_line = clean_section.split("\n")[0].replace("#", "").strip()
        
        chunk_obj = {
            "chunk_id": f"{source_file}#section_{idx}",
            "source_file": source_file,
            "section_title": first_line,
            "char_count": len(clean_section),
            "content": clean_section
        }
        chunks.append(chunk_obj)
        
    return chunks


def chunk_document_fixed_size(doc: dict, chunk_size: int = 200, overlap: int = 40) -> list[dict]:
    """
    STRATEGY 2 (BENCHMARK): Fixed-size Sliding Window Chunking.
    Splits text every N characters regardless of headings.
    """
    raw_content = doc["content"]
    source_file = doc["source_file"]
    
    chunks = []
    step = chunk_size - overlap
    chunk_idx = 1
    
    for i in range(0, len(raw_content), step):
        text_segment = raw_content[i : i + chunk_size]
        if not text_segment.strip():
            continue
            
        chunk_obj = {
            "chunk_id": f"{source_file}#fixed_{chunk_idx}",
            "source_file": source_file,
            "section_title": "Fixed Chunk",
            "char_count": len(text_segment),
            "content": text_segment
        }
        chunks.append(chunk_obj)
        chunk_idx += 1
        
        if i + chunk_size >= len(raw_content):
            break
            
    return chunks


if __name__ == "__main__":
    print("=== STEP 2: CHUNKING & OVERLAP TEST ===\n")
    
    # 1. Ingest documents from Step 1
    docs = load_markdown_documents(DOCS_DIR)
    
    print("=" * 60)
    print("STRATEGY 1: SECTION-BASED CHUNKING (Primary Strategy)")
    print("=" * 60)
    
    all_section_chunks = []
    for doc in docs:
        section_chunks = chunk_document_by_sections(doc)
        all_section_chunks.extend(section_chunks)
        print(f"\n📄 File '{doc['source_file']}' split into {len(section_chunks)} Section Chunk(s):")
        for c in section_chunks:
            print(f"   - Chunk ID: [{c['chunk_id']}] | Title: '{c['section_title']}' ({c['char_count']} chars)")
            
    print(f"\n✅ Total Section Chunks Generated across all docs: {len(all_section_chunks)}")
    print("\nSample Section Chunk Content:")
    print("-" * 50)
    print(all_section_chunks[1]["content"])
    print("-" * 50)
