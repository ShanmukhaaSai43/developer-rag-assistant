"""
===================================================================
STEP 1: Document Integration & Ingestion (Fermentation Recipes)
===================================================================
GOAL: Load raw Markdown recipe cards from disk (docs/ directory) 
      and extract structured metadata (source_file, recipe_id, cuisine, dietary_tags).
"""

import re
from pathlib import Path

# Path to our documentation directory
DOCS_DIR = Path(__file__).parent.parent / "docs"


def parse_frontmatter(raw_text: str) -> tuple[dict, str]:
    """
    Extracts YAML frontmatter metadata from markdown files.
    Returns (metadata_dict, clean_content).
    """
    metadata = {}
    content = raw_text
    
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw_text, re.DOTALL)
    if frontmatter_match:
        yaml_block = frontmatter_match.group(1)
        content = frontmatter_match.group(2)
        
        for line in yaml_block.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip()] = val.strip()
                
    return metadata, content


def load_markdown_documents(docs_directory: Path) -> list[dict]:
    """
    Reads all .md files in docs_directory and extracts raw documents with metadata.
    Requirement: Every chunk/doc MUST retain source_file, recipe_id, cuisine, dietary_tags.
    """
    documents = []
    
    md_files = list(docs_directory.glob("*.md"))
    print(f"[STEP 1 - INGESTION] Scanning folder '{docs_directory}'...")
    print(f"Found {len(md_files)} Markdown file(s) for ingestion.\n")
    
    for file_path in md_files:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
        metadata, content = parse_frontmatter(raw_text)
        
        doc_obj = {
            "source_file": metadata.get("source_file", file_path.name),
            "recipe_id": metadata.get("recipe_id", file_path.stem),
            "cuisine": metadata.get("cuisine", "general"),
            "dietary_tags": metadata.get("dietary_tags", "none"),
            "file_path": str(file_path),
            "char_count": len(content),
            "content": content
        }
        documents.append(doc_obj)
        
        print(f"📄 Loaded Recipe: '{doc_obj['source_file']}' (ID: {doc_obj['recipe_id']})")
        print(f"   - Cuisine:      {doc_obj['cuisine']}")
        print(f"   - Dietary Tags: {doc_obj['dietary_tags']}")
        print(f"   - Total Chars:  {len(content)} characters\n")
        
    return documents


if __name__ == "__main__":
    print("=== STEP 1: RECIPE DOCUMENT INGESTION TEST ===\n")
    ingested_docs = load_markdown_documents(DOCS_DIR)
    
    print(f"✅ Ingestion Complete! Successfully loaded {len(ingested_docs)} recipe document(s) into memory.")
    print("Ready for Step 2: Section-based Chunking & Metadata Preservation!")
