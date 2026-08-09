"""
===================================================================
STEP 1: Document Integration & Ingestion
===================================================================
GOAL: Load raw Markdown documentation from disk (docs/ directory) 
      and prepare structured Document objects with source metadata.

Key Concepts:
- In production, data comes from files on disk (.md, .pdf, .txt).
- Every ingested section MUST retain source metadata (file path, title).
"""

import os
from pathlib import Path

# Path to our documentation directory
DOCS_DIR = Path(__file__).parent.parent / "docs"


def load_markdown_documents(docs_directory: Path) -> list[dict]:
    """
    Reads all .md files in docs_directory and extracts raw documents.
    Returns a list of dictionaries containing file metadata and content.
    """
    documents = []
    
    # 1. Scan directory for .md files
    md_files = list(docs_directory.glob("*.md"))
    print(f"[STEP 1 - INGESTION] Scanning folder '{docs_directory}'...")
    print(f"Found {len(md_files)} Markdown file(s) for ingestion.\n")
    
    for file_path in md_files:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
        # Create a structured Document metadata object
        doc_obj = {
            "source_file": file_path.name,
            "file_path": str(file_path),
            "char_count": len(raw_text),
            "content": raw_text
        }
        documents.append(doc_obj)
        
        print(f"📄 Loaded Document: '{file_path.name}'")
        print(f"   - File Path:   {file_path}")
        print(f"   - Total Chars: {len(raw_text)} characters\n")
        
    return documents


if __name__ == "__main__":
    print("=== STEP 1: DOCUMENT INGESTION TEST ===\n")
    ingested_docs = load_markdown_documents(DOCS_DIR)
    
    print(f"✅ Ingestion Complete! Successfully loaded {len(ingested_docs)} document(s) into memory.")
    print("Ready for Step 2: Section-based Chunking & Overlap!")
