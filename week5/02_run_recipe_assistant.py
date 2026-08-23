"""
===================================================================
WEEK 5: Live Recipe Assistant with Full Trace Logging
===================================================================
Executes realistic recipe queries across our food knowledge base
and records complete, self-contained JSONL traces for error analysis.
===================================================================
"""

import os
import sys
import time
import uuid
from pathlib import Path
from dotenv import load_dotenv
from google import genai

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from week5.trace_system import CompleteTracer, PROMPT_VERSION, SYSTEM_INSTRUCTION

# Load environment
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

DOCS_DIR = ROOT_DIR / "docs"
WEEK4_DOCS_DIR = ROOT_DIR / "week4" / "docs"

# Load retrieval components
import importlib.util
step1 = importlib.util.spec_from_file_location("step1", ROOT_DIR / "src" / "01_ingest_docs.py").loader.load_module()
step2 = importlib.util.spec_from_file_location("step2", ROOT_DIR / "src" / "02_chunk_docs.py").loader.load_module()
step3 = importlib.util.spec_from_file_location("step3", ROOT_DIR / "src" / "03_embed_docs.py").loader.load_module()
step4 = importlib.util.spec_from_file_location("step4", ROOT_DIR / "src" / "04_vector_db.py").loader.load_module()
step5 = importlib.util.spec_from_file_location("step5", ROOT_DIR / "src" / "05_retrieval.py").loader.load_module()

class ProductionRecipeRAGAssistant:
    def __init__(self, score_threshold: float = 0.55):
        self.score_threshold = score_threshold
        self.ai_client = genai.Client(api_key=GEMINI_KEY)
        self.tracer = CompleteTracer()

        # Ingest docs from both docs/ and week4/docs/
        docs = step1.load_markdown_documents(DOCS_DIR)
        if WEEK4_DOCS_DIR.exists():
            docs.extend(step1.load_markdown_documents(WEEK4_DOCS_DIR))
        
        # Deduplicate docs by filename
        unique_docs = list({d["metadata"]["source_file"]: d for d in docs}.values())

        all_chunks = []
        for doc in unique_docs:
            all_chunks.extend(step2.chunk_document_by_sections(doc))

        self.embedder = step3.BGETextEmbeddingGenerator(model_name="BAAI/bge-small-en-v1.5")
        embedded_chunks = self.embedder.generate_embeddings(all_chunks)

        self.vector_db = step4.LocalVectorStoreHNSW(collection_name="week5_production_traces")
        self.vector_db.add_chunks(embedded_chunks)
        self.retriever = step5.DenseRetriever(vector_store=self.vector_db, embedder=self.embedder)

    def process_query(self, user_query: str, trace_id: str = None, top_k: int = 3, temperature: float = 0.0) -> dict:
        if not trace_id:
            trace_id = f"tr_{uuid.uuid4().hex[:8]}"

        start_time = time.perf_counter()

        # 1. Retrieve
        retrieved_chunks = self.retriever.retrieve(
            user_query=user_query,
            top_k=top_k,
            score_threshold=self.score_threshold
        )

        refusal_triggered = len(retrieved_chunks) == 0

        # 2. Build Prompt
        if refusal_triggered:
            formatted_prompt = f"{SYSTEM_INSTRUCTION}\n\nContext:\n[NO CONTEXT FOUND]\n\nUser Question: {user_query}\nAnswer:"
            raw_output = "I cannot find information about this in the provided recipe documentation."
            model_name = "gemini-2.5-flash"
        else:
            context_blocks = []
            for c in retrieved_chunks:
                source_tag = f"[{c['source_file']}#{c['section_title']}]"
                context_blocks.append(f"Source {source_tag}:\n{c['content']}")
            context_str = "\n\n".join(context_blocks)

            formatted_prompt = f"{SYSTEM_INSTRUCTION}\n\nContext:\n{context_str}\n\nUser Question: {user_query}\nAnswer:"
            model_name = "gemini-2.5-flash"

            try:
                response = self.ai_client.models.generate_content(
                    model=model_name,
                    contents=formatted_prompt,
                    config={"temperature": temperature}
                )
                raw_output = response.text.strip() if response.text else ""
            except Exception as e:
                # Fallback model if needed
                try:
                    response = self.ai_client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=formatted_prompt
                    )
                    model_name = "gemini-2.0-flash"
                    raw_output = response.text.strip() if response.text else ""
                except Exception as e2:
                    raw_output = f"ERROR: Generation failed ({e2})"

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 3. Emit Complete Trace
        trace = self.tracer.log_trace(
            trace_id=trace_id,
            user_query=user_query,
            retrieved_chunks=retrieved_chunks,
            model_name=model_name,
            model_params={"temperature": temperature, "top_p": 0.95, "max_tokens": 1024},
            formatted_prompt=formatted_prompt,
            raw_output=raw_output,
            latency_ms=latency_ms,
            refusal_triggered=refusal_triggered
        )
        return trace


if __name__ == "__main__":
    assistant = ProductionRecipeRAGAssistant()
    print("Ready to process recipe queries and emit structured traces.")
