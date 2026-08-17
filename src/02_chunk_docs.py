"""
===================================================================
STEP 2: Section-Based & Fixed-Size Chunking (Task Set B)
===================================================================
GOAL: Take ingested recipe cards and test TWO chunking strategies:
1. Strategy 1 (Structure-Aware / Section-Based): Keeps recipe title, ingredient table, 
   and method prose in their dedicated header blocks.
2. Strategy 2 (Fixed-Size / Sliding Window): Naive character split (size=250, overlap=50).

Requirement: Every chunk MUST carry source_file, recipe_id, cuisine, dietary_tags.
"""

import re
import importlib.util
from pathlib import Path

# Dynamically import Step 1 module
DOCS_DIR = Path(__file__).parent.parent / "docs"
step1_path = Path(__file__).parent / "01_ingest_docs.py"
spec = importlib.util.spec_from_file_location("step1_module", step1_path)
step1_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step1_module)
load_markdown_documents = step1_module.load_markdown_documents


def chunk_document_by_sections(doc: dict) -> list[dict]:
    """
    STRATEGY 1 (STRUCTURE-AWARE): Section-Based Chunking.
    Splits document on '## ' section headings so ingredient tables and methods remain unbroken.
    Inherits all metadata: source_file, recipe_id, cuisine, dietary_tags.
    """
    raw_content = doc["content"]
    source_file = doc["source_file"]
    recipe_id = doc.get("recipe_id", "unknown")
    cuisine = doc.get("cuisine", "general")
    dietary_tags = doc.get("dietary_tags", "none")
    
    sections = re.split(r'\n(?=##\s+)', raw_content)
    
    chunks = []
    for idx, section in enumerate(sections, 1):
        clean_section = section.strip()
        if not clean_section:
            continue
            
        first_line = clean_section.split("\n")[0].replace("#", "").strip()
        
        chunk_obj = {
            "chunk_id": f"{recipe_id}#section_{idx}",
            "source_file": source_file,
            "recipe_id": recipe_id,
            "cuisine": cuisine,
            "dietary_tags": dietary_tags,
            "section_title": first_line,
            "char_count": len(clean_section),
            "content": clean_section
        }
        chunks.append(chunk_obj)
        
    return chunks


def chunk_document_fixed_size(doc: dict, chunk_size: int = 250, overlap: int = 50) -> list[dict]:
    """
    STRATEGY 2 (NAIVE FIXED-SIZE): Sliding Window Chunking.
    Splits text every 250 chars with 50 char overlap regardless of tables or headings.
    Inherits all metadata: source_file, recipe_id, cuisine, dietary_tags.
    """
    raw_content = doc["content"]
    source_file = doc["source_file"]
    recipe_id = doc.get("recipe_id", "unknown")
    cuisine = doc.get("cuisine", "general")
    dietary_tags = doc.get("dietary_tags", "none")
    
    chunks = []
    step = chunk_size - overlap
    chunk_idx = 1
    
    for i in range(0, len(raw_content), step):
        text_segment = raw_content[i : i + chunk_size]
        if not text_segment.strip():
            continue
            
        chunk_obj = {
            "chunk_id": f"{recipe_id}#fixed_{chunk_idx}",
            "source_file": source_file,
            "recipe_id": recipe_id,
            "cuisine": cuisine,
            "dietary_tags": dietary_tags,
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
    print("=== STEP 2: CHUNKING & OVERLAP TEST (RECIPES) ===\n")
    
    docs = load_markdown_documents(DOCS_DIR)
    
    print("=" * 60)
    print("STRATEGY 1: STRUCTURE-AWARE SECTION CHUNKING")
    print("=" * 60)
    
    all_section_chunks = []
    for doc in docs:
        section_chunks = chunk_document_by_sections(doc)
        all_section_chunks.extend(section_chunks)
        print(f"\n📄 Recipe '{doc['recipe_id']}' split into {len(section_chunks)} Section Chunk(s):")
        for c in section_chunks:
            print(f"   - Chunk ID: [{c['chunk_id']}] | Title: '{c['section_title']}' | Tags: {c['dietary_tags']}")
            
    print(f"\n✅ Total Section Chunks: {len(all_section_chunks)}")
