"""
===================================================================
WEEK 4: Corpus Ingestion, Section Chunking & Indexing
===================================================================
Loads recipe markdown documents, chunks them by section header, 
stores dense embeddings in ChromaDB, and prepares the corpus metadata.
"""

import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

WEEK4_DIR = Path(__file__).parent.parent
DOCS_DIR = WEEK4_DIR / "docs"
CHROMA_DIR = WEEK4_DIR / ".chroma_db"
COLLECTION_NAME = "week4_recipe_corpus"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML-style frontmatter headers from markdown files."""
    frontmatter = {}
    body = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body = parts[2].strip()
            for line in fm_text.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    frontmatter[key.strip()] = val.strip()
                    
    return frontmatter, body


def load_markdown_documents(docs_dir: Path) -> list[dict]:
    """Reads all markdown files from the docs directory."""
    documents = []
    for file_path in sorted(docs_dir.glob("*.md")):
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
        frontmatter, clean_body = parse_frontmatter(raw_text)
        
        doc_obj = {
            "source_file": file_path.name,
            "recipe_id": frontmatter.get("recipe_id", file_path.stem),
            "cuisine": frontmatter.get("cuisine", "general"),
            "dietary_tags": frontmatter.get("dietary_tags", "none"),
            "content": clean_body,
            "raw_content": raw_text
        }
        documents.append(doc_obj)
        
    return documents


def chunk_document_by_sections(doc: dict) -> list[dict]:
    """
    Structure-Aware Section Chunking:
    Splits recipe on '## ' headers and prepends parent recipe title so every chunk
    retains clear contextual grounding.
    """
    raw_content = doc["content"]
    source_file = doc["source_file"]
    recipe_id = doc.get("recipe_id", "unknown")
    cuisine = doc.get("cuisine", "general")
    dietary_tags = doc.get("dietary_tags", "none")
    
    # Extract main H1 recipe title
    h1_match = re.search(r'^#\s+(.+)$', raw_content, re.MULTILINE)
    h1_title = h1_match.group(1).strip() if h1_match else recipe_id
    
    sections = re.split(r'\n(?=##\s+)', raw_content)
    chunks = []
    
    chunk_idx = 1
    for section in sections:
        clean_section = section.strip()
        if not clean_section:
            continue
            
        first_line = clean_section.split("\n")[0].replace("#", "").strip()
        
        # Don't create standalone 1-line chunk for just the H1 header
        if clean_section.startswith("# ") and "##" not in clean_section and len(clean_section.splitlines()) <= 2:
            continue
            
        # Ensure section text includes the recipe name for semantic & sparse index clarity
        chunk_content = clean_section
        if not chunk_content.startswith("# "):
            chunk_content = f"[{h1_title}] {clean_section}"
        
        chunk_obj = {
            "chunk_id": f"{recipe_id}#section_{chunk_idx}",
            "source_file": source_file,
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


def build_and_save_index():
    """Builds both the ChromaDB dense index and the JSON corpus cache."""
    print("=" * 60)
    print("WEEK 4 INGESTION: Building Dense & Sparse Corpus Indices")
    print("=" * 60)
    
    docs = load_markdown_documents(DOCS_DIR)
    print(f"Loaded {len(docs)} markdown recipe document(s) from '{DOCS_DIR.name}'")
    
    all_chunks = []
    for doc in docs:
        chunks = chunk_document_by_sections(doc)
        all_chunks.extend(chunks)
        print(f" - {doc['recipe_id']}: {len(chunks)} chunks")
        
    print(f"\nTotal Chunks Created: {len(all_chunks)}")
    
    # Save corpus JSON for BM25 and Inspection View
    corpus_cache_path = WEEK4_DIR / "corpus_chunks.json"
    with open(corpus_cache_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)
    print(f"[OK] Saved corpus chunk cache to '{corpus_cache_path.name}'")
    
    # Generate Dense Embeddings with FastEmbed (bge-small-en-v1.5)
    print("\nInitializing FastEmbed ('BAAI/bge-small-en-v1.5')...")
    from fastembed import TextEmbedding
    embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    texts = [c["content"] for c in all_chunks]
    print(f"Generating dense embeddings for {len(texts)} chunks...")
    embeddings = [list(map(float, vec)) for vec in embedder.embed(texts)]
    
    # Store in ChromaDB
    import chromadb
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Reset/Create collection
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
        
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    ids = [c["chunk_id"] for c in all_chunks]
    metadatas = [{
        "chunk_id": c["chunk_id"],
        "source_file": c["source_file"],
        "recipe_id": c["recipe_id"],
        "cuisine": c["cuisine"],
        "dietary_tags": c["dietary_tags"],
        "section_title": c["section_title"],
        "char_count": c["char_count"]
    } for c in all_chunks]
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=texts
    )
    
    print(f"[OK] Successfully indexed {collection.count()} chunks into ChromaDB ({COLLECTION_NAME})")
    return all_chunks


if __name__ == "__main__":
    build_and_save_index()
