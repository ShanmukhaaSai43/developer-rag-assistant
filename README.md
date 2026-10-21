# 🍽️ Week 12 Capstone: Pantry-to-Plate Assistant (Variant B)

> Production-grade, allergy-safe culinary agent integrating **MCP Tools over JSON-RPC 2.0**, **Structured SQLite Recipe Ledger**, **Distributed Telemetry with Health PII Masking**, **Two-Stage Safety Evaluations**, and a **Closed Failure-to-Test Loop**.

### ⚡ Single-Command Quickstart (Stranger Ready)
```bash
# 1. Ask any cooking or allergen safety question:
.venv/Scripts/python.exe -m week12.main --query "Is the 2025 Scottish shortbread safe for someone with a tree nut allergy?"

# 2. Run the Full 30-Case Evaluation Suite (Stage 1 Assertions + Stage 2 LLM Judge):
.venv/Scripts/python.exe -m week12.main --eval

# 3. Run the 12-Case Trajectory Benchmark (Computes Tool-Choice Accuracy & Outcome-vs-Trajectory Gap):
.venv/Scripts/python.exe -m week12.main --trajectory

# 4. Run the Closed Failure-to-Test Loop Demonstration (RED failure -> GREEN permanent guard):
.venv/Scripts/python.exe -m week12.main --closed-loop

# 5. Launch the React Web UI & Backend API on http://127.0.0.1:8000:
.venv/Scripts/python.exe -m week12.main --ui

# 6. Or run the React Vite Dev Server (Hot-Reloading on http://localhost:5173):
cd pantry-ui && npm run dev
```

### 📋 Week 12 Artifact Deliverables
| Rubric Deliverable | File Path | Status |
|:---|:---|:---:|
| **Single Entry Point** | [`week12/main.py`](week12/main.py) | Verified |
| **Evaluation Report** | [`week12/eval_report.md`](week12/eval_report.md) | Verified (96.7% Judge Agreement, -83.3% Allergen Drop) |
| **Failure Taxonomy** | [`week12/taxonomy.md`](week12/taxonomy.md) | 10 Modes Re-Scored + Downstream Substitution |
| **Trajectory Evaluation** | [`week12/trajectory_eval.py`](week12/trajectory_eval.py) | Verified (+25.0% Outcome-vs-Trajectory Gap) |
| **Closed Failure Loop** | [`week12/closed_loop_test.py`](week12/closed_loop_test.py) | Verified (RED -> GREEN permanent guard) |
| **Distributed Trace Sample** | [`week12/trace_sample.json`](week12/trace_sample.json) | Complete 5-Span Trace ($0.000349, Health PII Masked) |
| **10× Scaling Plan** | [`week12/tenx_plan.md`](week12/tenx_plan.md) | Cost Analysis ($17.45/day for 50k queries) |
| **Top 3 Weaknesses** | [`week12/weaknesses.md`](week12/weaknesses.md) | Dated Wednesday |
| **System Architecture** | [`week12/architecture.md`](week12/architecture.md) | 1-Page ASCII Architecture |
| **Squad 4 Peer Audit** | [`week12/fresh_eyes_note.md`](week12/fresh_eyes_note.md) | Priya S. Audit Note |
| **10-Min Demo Script** | [`week12/demo_script.md`](week12/demo_script.md) | Covers 4-Part Standard |

---

# 🚀 Developer Documentation RAG Assistant (Earlier Modules)

An end-to-end **Retrieval-Augmented Generation (RAG)** pipeline for technical developer documentation powered by **Google Gemini Neural Embeddings** (`gemini-embedding-001`), **Vector Similarity Search**, and **Live Gemini LLM Generation** (`gemini-3.6-flash`).

Built with strict **grounding guardrails**, **exact source citations**, and **zero-hallucination refusals**.

---

## 🏗️ 6-Step RAG Pipeline Architecture

```text
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────────┐
│ Step 1: Ingest  │ ────► │  Step 2: Chunk  │ ────► │   Step 3: Embed     │
│ Raw Markdown    │       │  Section-Based  │       │ Gemini Neural Model │
│ Docs + Metadata │       │  Heading Splits │       │ (768-dim Vectors)   │
└─────────────────┘       └─────────────────┘       └─────────────────────┘
                                                               │
                                                               ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────────┐
│  Step 6: Answer │ ◄──── │ Step 5: Retrieve│ ◄──── │ Step 4: Vector Store│
│ Grounded Gemini │       │ Top-K Dense     │       │ Cosine Similarity   │
│ LLM + Citations │       │ Similarity      │       │ HNSW Storage        │
└─────────────────┘       └─────────────────┘       └─────────────────────┘
```

---

## 📂 Project Structure

```text
Demo/
├── docs/                      # Raw developer markdown documentation corpus
│   ├── api_reference.md       # API specs & Webhooks docs
│   ├── company_policies.md    # Rate limits & return policies
│   └── developer_rag_docs.md  # AuthSDK reference guide
├── src/                       # Modular 6-Step RAG Pipeline
│   ├── 01_ingest_docs.py      # Step 1: Ingestion & metadata extraction
│   ├── 02_chunk_docs.py       # Step 2: Section-based heading chunking
│   ├── 03_embed_docs.py       # Step 3: Google Gemini neural embedding generation
│   ├── 04_vector_db.py        # Step 4: Vector store & indexing engine
│   ├── 05_retrieval.py        # Step 5: Dense retrieval & top-K similarity search
│   └── 06_grounded_generation.py # Step 6: Live LLM grounded generation & refusals
├── .env.example               # Template for required environment variables
├── pyproject.toml             # Python dependencies configuration
└── README.md                  # Project documentation
```

---

## ⚡ Quick Start & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/developer-rag-assistant.git
cd developer-rag-assistant
```

### 2. Environment Configuration
Create a `.env` file in the project root and add your Google Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 3. Install Dependencies
Using `uv` (recommended):
```bash
uv sync
```
Or using standard `pip`:
```bash
pip install -r pyproject.toml
```

---

## 🧪 Running the Pipeline

You can run individual step scripts or the full end-to-end RAG assistant:

### Run Full RAG Assistant (Step 6)
```bash
.venv/Scripts/python.exe src/06_grounded_generation.py
```

### Test Individual Pipeline Steps
```bash
# Step 1: Test Ingestion
.venv/Scripts/python.exe src/01_ingest_docs.py

# Step 2: Test Section Chunking
.venv/Scripts/python.exe src/02_chunk_docs.py

# Step 3: Test Gemini Embedding Generation
.venv/Scripts/python.exe src/03_embed_docs.py

# Step 4: Test Vector Store Indexing
.venv/Scripts/python.exe src/04_vector_db.py

# Step 5: Test Vector Retrieval & Similarity Search
.venv/Scripts/python.exe src/05_retrieval.py
```

---

## 🛡️ Key Safety Features

- **Strict Refusal Guardrail:** Questions scoring below similarity threshold (`0.60`) trigger an immediate refusal without calling the LLM API, preventing hallucinations and reducing token costs.
- **Fact-Grounded Generation:** System prompts restrict the model to use **only** facts explicitly stated in the retrieved context.
- **Source Citations:** Answers automatically include exact source citations formatted as `[filename.md#Section Title]`.

---

## 📄 License
MIT License
