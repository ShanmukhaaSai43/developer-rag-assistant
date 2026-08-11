"""
===================================================================
STEP 3: Embedding Model Selection & Dense Vector Generation
===================================================================
GOAL: Convert Section Chunks from Step 2 into Dense Vector Embeddings.

Supported Engines:
1. BAAI BGE Model ('BAAI/bge-small-en-v1.5'): 384-dim 100% Local CPU Embedding.
2. Google Gemini Model ('gemini-embedding-001'): 768-dim Cloud Neural Vector.
"""

import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import importlib.util
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Dynamically import Step 1 & Step 2 modules
DOCS_DIR = Path(__file__).parent.parent / "docs"
step1_path = Path(__file__).parent / "01_ingest_docs.py"
step2_path = Path(__file__).parent / "02_chunk_docs.py"

spec1 = importlib.util.spec_from_file_location("step1_module", step1_path)
step1_module = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(step1_module)

spec2 = importlib.util.spec_from_file_location("step2_module", step2_path)
step2_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(step2_module)

load_markdown_documents = step1_module.load_markdown_documents
chunk_document_by_sections = step2_module.chunk_document_by_sections


class BGETextEmbeddingGenerator:
    """
    Generates 384-dimensional dense neural vectors 100% locally on CPU
    using FastEmbed and BAAI/bge-small-en-v1.5.
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        print(f"[STEP 3 - EMBEDDING] Initializing Local BGE Model '{model_name}'...")
        from fastembed import TextEmbedding
        self.model_name = model_name
        self.model = TextEmbedding(model_name=model_name)
        print("✅ Local BGE Neural Embeddings initialized successfully!")

    def generate_embeddings(self, chunks: list[dict]) -> list[dict]:
        """
        Takes chunk dicts, generates 384-dim neural vectors, and attaches 'vector' key.
        """
        print(f"Generating 384-dim dense BGE neural vectors for {len(chunks)} chunk(s)...")
        texts = [c["content"] for c in chunks]
        embeddings = list(self.model.embed(texts))
        
        for idx, chunk in enumerate(chunks):
            chunk["vector"] = [float(v) for v in embeddings[idx]]
            
        return chunks

    def embed_query(self, query_text: str) -> list[float]:
        """
        Embeds a single query string for vector search.
        """
        embeddings = list(self.model.embed([query_text]))
        return [float(v) for v in embeddings[0]]


class GeminiNeuralEmbeddingGenerator:
    """
    Generates 768-dimensional dense neural vectors using Google Gemini API.
    """
    def __init__(self, model_name: str = "gemini-embedding-001"):
        print(f"[STEP 3 - EMBEDDING] Initializing Google Neural Model '{model_name}'...")
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not self.gemini_key or self.gemini_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY not found in .env file!")
            
        from google import genai
        self.client = genai.Client(api_key=self.gemini_key)
        self.model_name = model_name
        print("✅ Google Gemini Neural Embeddings initialized successfully!")

    def generate_embeddings(self, chunks: list[dict]) -> list[dict]:
        """
        Takes chunk dicts, generates 768-dim neural vectors, and attaches 'vector' key.
        """
        print(f"Generating 768-dim dense neural vectors for {len(chunks)} chunk(s)...")
        
        for chunk in chunks:
            res = self.client.models.embed_content(
                model=self.model_name,
                contents=chunk["content"]
            )
            raw_values = res.embeddings[0].values
            chunk["vector"] = [float(v) for v in raw_values]
            
        return chunks

    def embed_query(self, query_text: str) -> list[float]:
        """
        Embeds a single query string for vector search.
        """
        res = self.client.models.embed_content(
            model=self.model_name,
            contents=query_text
        )
        return [float(v) for v in res.embeddings[0].values]


if __name__ == "__main__":
    print("=== STEP 3: DENSE NEURAL EMBEDDING GENERATION (Local BGE Model) ===\n")
    
    docs = load_markdown_documents(DOCS_DIR)
    
    all_chunks = []
    for doc in docs:
        section_chunks = chunk_document_by_sections(doc)
        all_chunks.extend(section_chunks)
        
    print(f"\nExtracted {len(all_chunks)} section chunks from ingested files.")
    
    embedder = BGETextEmbeddingGenerator(model_name="BAAI/bge-small-en-v1.5")
    embedded_chunks = embedder.generate_embeddings(all_chunks)
    
    print("\n✅ Step 3 Complete! Sample Neural Embedded Chunk Metadata:")
    print("=" * 65)
    sample = embedded_chunks[1]
    print(f"Chunk ID:          {sample['chunk_id']}")
    print(f"Source File:       {sample['source_file']}")
    print(f"Section Title:     {sample['section_title']}")
    print(f"Vector Dimensions: {len(sample['vector'])} floating-point numbers")
    print(f"First 5 Values:    {sample['vector'][:5]}")
    print("=" * 65)
