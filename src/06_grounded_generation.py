"""
===================================================================
STEP 6: Grounded LLM Generation, Citations & Strict Refusal
===================================================================
GOAL: Combine Neural Vector Retrieval (Step 5) with Live Gemini LLM
      Generation to provide grounded, factual answers with source citations.

Key Features:
1. Retrieval-Augmented Generation (RAG): Context chunks guide the LLM.
2. Strict Refusal Guardrail: If similarity score < threshold, refuse without LLM call.
3. Factual Grounding: Instructions prevent hallucinations.
4. Source Citations: Every claim cites the exact file & section title.
"""

import os
import importlib.util
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Dynamically import Steps 1-5 modules
DOCS_DIR = Path(__file__).parent.parent / "docs"
step1_path = Path(__file__).parent / "01_ingest_docs.py"
step2_path = Path(__file__).parent / "02_chunk_docs.py"
step3_path = Path(__file__).parent / "03_embed_docs.py"
step4_path = Path(__file__).parent / "04_vector_db.py"
step5_path = Path(__file__).parent / "05_retrieval.py"

def _import_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

step1 = _import_module("step1_module", step1_path)
step2 = _import_module("step2_module", step2_path)
step3 = _import_module("step3_module", step3_path)
step4 = _import_module("step4_module", step4_path)
step5 = _import_module("step5_module", step5_path)

load_markdown_documents = step1.load_markdown_documents
chunk_document_by_sections = step2.chunk_document_by_sections
BGETextEmbeddingGenerator = step3.BGETextEmbeddingGenerator
GeminiNeuralEmbeddingGenerator = step3.GeminiNeuralEmbeddingGenerator
LocalVectorStoreHNSW = step4.LocalVectorStoreHNSW
DenseRetriever = step5.DenseRetriever


class GroundedRAGAssistant:
    """
    Complete End-to-End RAG Pipeline:
    Vector Store + Dense Retrieval + Grounded LLM Generation + Refusals
    """
    def __init__(self, docs_dir: Path = DOCS_DIR, score_threshold: float = 0.60):
        self.score_threshold = score_threshold
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if not self.gemini_key or self.gemini_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY not found in .env file!")

        from google import genai
        self.ai_client = genai.Client(api_key=self.gemini_key)

        print("[STEP 6 - INITIALIZING FULL RAG SYSTEM]...")
        # 1. Ingest
        docs = load_markdown_documents(docs_dir)

        # 2. Chunk
        all_chunks = []
        for doc in docs:
            all_chunks.extend(chunk_document_by_sections(doc))

        # 3. Embed (Local BGE Model)
        self.embedder = BGETextEmbeddingGenerator(model_name="BAAI/bge-small-en-v1.5")
        embedded_chunks = self.embedder.generate_embeddings(all_chunks)

        # 4. Vector Store
        self.vector_db = LocalVectorStoreHNSW(collection_name="developer_docs_hnsw")
        self.vector_db.add_chunks(embedded_chunks)

        # 5. Retriever
        self.retriever = DenseRetriever(vector_store=self.vector_db, embedder=self.embedder)
        print("✅ Grounded RAG Assistant successfully initialized & indexed!\n")

    def answer_question(self, user_query: str, top_k: int = 2):
        """
        Executes full RAG workflow for a user query:
        Retrieves chunks -> Evaluates similarity threshold -> Generates cited response or Refuses.
        """
        print("=" * 70)
        print(f"❓ USER QUERY: '{user_query}'")
        print("=" * 70)

        # Step A: Dense Retrieval
        retrieved_chunks = self.retriever.retrieve(
            user_query=user_query,
            top_k=top_k,
            score_threshold=self.score_threshold
        )

        # Step B: Strict Refusal Check (Threshold Guardrail)
        if not retrieved_chunks:
            print(f"\n🚫 [REFUSAL TRIGGERED]: No document chunks matched above threshold ({self.score_threshold:.2f}).")
            print("\n=== GROUNDED AI ANSWER ===")
            print("ANSWER: I cannot find information about this in the provided documentation.")
            print("CITATION: N/A (Refused due to lack of source context)\n")
            return

        print(f"\n✅ Retrieved {len(retrieved_chunks)} relevant chunk(s) above threshold:")
        for r in retrieved_chunks:
            print(f"   - [{r['source_file']} # {r['section_title']}] (Similarity Score: {r['similarity_score']:.4f})")

        # Step C: Build Grounded Context Prompt
        context_blocks = []
        for c in retrieved_chunks:
            source_tag = f"[{c['source_file']}#{c['section_title']}]"
            context_blocks.append(f"Source {source_tag}:\n{c['content']}")

        context_str = "\n\n".join(context_blocks)

        rag_prompt = f"""You are an expert Developer Documentation Assistant. Answer the developer's question using ONLY the provided document context below.

STRICT RULES:
1. Answer using ONLY facts explicitly stated in the Context.
2. Every claim in your answer MUST end with a source citation matching the source tag, e.g., [{retrieved_chunks[0]['source_file']}#{retrieved_chunks[0]['section_title']}].
3. If the context does not contain enough information to answer, reply strictly: "I cannot find information about this in the documentation."
4. Do NOT use outside knowledge or speculate.

Context:
{context_str}

Developer Question: {user_query}
Answer:"""

        # Step D: Call Live Gemini LLM API
        print("\n🤖 [GENERATION]: Calling Live Gemini API for Grounded Answer...")
        for model_name in ["gemini-3.6-flash", "gemini-2.0-flash"]:
            try:
                response = self.ai_client.models.generate_content(
                    model=model_name,
                    contents=rag_prompt
                )
                print(f"\n=== GROUNDED AI ANSWER ({model_name}) ===")
                print(response.text)
                print("=" * 70 + "\n")
                return
            except Exception as e:
                if "429" in str(e):
                    continue
                print(f"⚠️ Generation error with {model_name}: {e}")
                return


if __name__ == "__main__":
    print("=== STEP 6: GROUNDED GENERATION & REFUSAL SYSTEM TEST ===\n")

    assistant = GroundedRAGAssistant(score_threshold=0.60)

    # Test 1: In-Domain Recipe Query (Ingredient Table)
    assistant.answer_question("What is the exact fine sea salt weight and percentage for the country sourdough loaf?")

    # Test 2: In-Domain Recipe Query (Fermentation Step)
    assistant.answer_question("What temperature range and duration are required for primary fermentation of kombucha?")

    # Test 3: Out-of-Domain Query (Should Refuse)
    assistant.answer_question("What is the total calorie count and carbohydrate breakdown per slice of sourdough bread?")
