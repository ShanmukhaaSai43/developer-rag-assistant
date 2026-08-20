"""
===================================================================
WEEK 4 · PRACTICE LAB: Query Rewriting & HyDE (Hypothetical Document Embeddings)
===================================================================
PURPOSE:
A standalone practice script to demonstrate:
1. Query Rewriting: Resolving ambiguous / conversational user queries into keyword-rich search terms.
2. HyDE (Hypothetical Document Embeddings): Using an LLM to generate a hypothetical answer document first,
   then embedding that document to retrieve matching real chunks from ChromaDB.

* Standalone file for local learning and experimentation.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from fastembed import TextEmbedding
from google import genai

load_dotenv()

WEEK4_DIR = Path(__file__).parent
CHROMA_DIR = WEEK4_DIR / ".chroma_db"
COLLECTION_NAME = "week4_recipe_corpus"


# ===================================================================
# 1. SETUP GEMINI CLIENT (FOR GENERATING REWRITES & HYPOTHETICAL DOCS)
# ===================================================================
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[WARNING] GEMINI_API_KEY not found in .env. LLM generation will use mock responses.")
        return None
    return genai.Client(api_key=api_key)


# ===================================================================
# 2. QUERY REWRITER IMPLEMENTATION
# ===================================================================
class QueryRewriter:
    """
    Takes messy, vague, conversational, or multi-turn queries and rewrites
    them into clear, entity-rich queries optimized for search retrievers.
    """
    def __init__(self, client=None):
        self.client = client

    def rewrite(self, user_query: str, chat_history: str = "") -> str:
        prompt = f"""You are an expert search query optimizer for a culinary fermentation recipe system.
Your job is to rewrite the user query into a single, highly specific, standalone search query.
- Resolve any pronouns ('it', 'that step', 'the other recipe').
- Fix spelling mistakes.
- Include essential domain terms (temperatures, ingredients, fermentation steps).
- Return ONLY the rewritten query string, nothing else.

Chat Context (if any):
{chat_history if chat_history else "None"}

User Query: "{user_query}"
Rewritten Search Query:"""

        if self.client:
            for model_name in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    if response and response.text:
                        return response.text.strip().strip('"')
                except Exception as e:
                    continue

        # Fallback simulation of an intelligent query rewrite
        return "garlic dill pickles oak grape tannin leaves crispness measurement"


# ===================================================================
# 3. HyDE (HYPOTHETICAL DOCUMENT EMBEDDINGS) IMPLEMENTATION
# ===================================================================
class HyDERetriever:
    """
    HyDE Workflow:
    1. User Question -> LLM generates a HYPOTHETICAL answer document.
    2. Embed the HYPOTHETICAL document (Document-to-Document matching).
    3. Query ChromaDB with the hypothetical embedding.
    """
    def __init__(self, collection, embedder, client=None):
        self.collection = collection
        self.embedder = embedder
        self.client = client

    def generate_hypothetical_document(self, query: str) -> str:
        prompt = f"""You are a master fermentation chef.
Write a short 2-sentence recipe manual excerpt that directly answers: "{query}".
Write only the excerpt."""

        if self.client:
            for model_name in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    continue

        # Fallback hypothetical document passage
        return "Naturally fermented garlic dill pickles require fresh oak or grape leaves containing natural tannins to inhibit pectinase enzymes and maintain a crisp, crunchy texture throughout fermentation."

    def search_with_hyde(self, query: str, top_k: int = 3) -> tuple[list[dict], str]:
        # Step 1: Generate hypothetical answer
        hypo_doc = self.generate_hypothetical_document(query)

        # Step 2: Embed the hypothetical document
        hypo_vec = [list(map(float, vec)) for vec in self.embedder.embed([hypo_doc])][0]

        # Step 3: Query vector DB with the hypothetical document embedding
        res = self.collection.query(
            query_embeddings=[hypo_vec],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        results = []
        if res and res["ids"]:
            for rank, (cid, meta, doc, dist) in enumerate(zip(
                res["ids"][0], res["metadatas"][0], res["documents"][0], res["distances"][0]
            ), 1):
                item = dict(meta)
                item["chunk_id"] = cid
                item["content"] = doc
                item["rank"] = rank
                item["sim"] = round(max(0.0, 1.0 - dist), 4)
                results.append(item)

        return results, hypo_doc


# ===================================================================
# 4. DEMO RUNNER (COMPARING STANDARD vs. REWRITE vs. HyDE)
# ===================================================================
def run_practice_demo():
    print("=" * 85)
    print("DEMO: QUERY REWRITING & HyDE IN ACTION")
    print("=" * 85)

    client = get_gemini_client()
    embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_collection(name=COLLECTION_NAME)

    rewriter = QueryRewriter(client)
    hyde = HyDERetriever(collection, embedder, client)

    # -----------------------------------------------------------------
    # EXPERIMENT 1: Query Rewriting on a Vague / Conversational Query
    # -----------------------------------------------------------------
    vague_query = "how much of it for the crunchy pickle step?"
    chat_context = "User previously asked about naturally fermented garlic dill pickles."

    print("\n" + "-" * 85)
    print("1. QUERY REWRITING EXPERIMENT")
    print("-" * 85)
    print(f"Original Vague Query: \"{vague_query}\"")
    print(f"Chat Context:         \"{chat_context}\"")

    rewritten = rewriter.rewrite(vague_query, chat_history=chat_context)
    print(f"\n-> Rewritten Search Query: \"{rewritten}\"")

    # -----------------------------------------------------------------
    # EXPERIMENT 2: HyDE on a Conceptual Question
    # -----------------------------------------------------------------
    conceptual_query = "What keeps fermented pickles from turning soft and mushy?"

    print("\n" + "-" * 85)
    print("2. HyDE (HYPOTHETICAL DOCUMENT EMBEDDINGS) EXPERIMENT")
    print("-" * 85)
    print(f"Original Query: \"{conceptual_query}\"")

    # A) Standard Query Embedding Search
    q_vec = [list(map(float, vec)) for vec in embedder.embed([conceptual_query])][0]
    std_res = collection.query(query_embeddings=[q_vec], n_results=3)
    std_ids = std_res["ids"][0] if std_res and std_res["ids"] else []

    print("\n[A] Standard Query Embedding Top-3 Results:")
    for rank, cid in enumerate(std_ids, 1):
        print(f"    #{rank} [{cid}]")

    # B) HyDE Search
    hyde_results, hypo_doc = hyde.search_with_hyde(conceptual_query, top_k=3)

    print(f"\n[B] HyDE Generated Passage Preview:")
    print(f"    \"{hypo_doc[:160].replace(chr(10), ' ')}...\"")

    print("\n[B] HyDE Document-to-Document Top-3 Results:")
    for r in hyde_results:
        print(f"    #{r['rank']} [{r['chunk_id']}] (Sim: {r['sim']}) - {r.get('section_title', '')}")

    print("\n" + "=" * 85)
    print("TAKEAWAYS:")
    print("1. Query Rewriter expands context and resolves ambiguities before search.")
    print("2. HyDE aligns query representations with document structure to improve conceptual retrieval.")
    print("=" * 85)


if __name__ == "__main__":
    run_practice_demo()
