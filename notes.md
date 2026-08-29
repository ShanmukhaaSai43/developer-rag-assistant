# Week 5: Practical Task Set B — Error Analysis & Trace Log Verification

**Domain:** Food Fermentation & Culinary Recipe Assistant  
**Pipeline:** Production RAG (Section Chunking, BAAI/bge-small-en-v1.5 Dense Embeddings, ChromaDB, Gemini LLM with Grounded Citations)  
**Artifacts Generated:** [`taxonomy.md`](file:///c:/Users/Admin/Documents/GenAi/Demo/taxonomy.md), [`week5/traces.jsonl`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl), [`week5/replay_evidence.json`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/replay_evidence.json)

---

## 1. Trace Logging Schema & Replay Verification Proof

### A. Trace Schema Definition
Every production interaction is logged as a self-contained JSON object to [`week5/traces.jsonl`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl) adhering to the following schema:
- `trace_id`: Unique deterministic hash identifying the interaction session.
- `timestamp`: ISO 8601 UTC timestamp.
- `user_query`: Exact raw user query string.
- `prompt_version`: Version identifier for the system instruction and prompt template (`v1.2.0_grounded_recipe`).
- `system_instruction`: System prompt instructions containing grounding, formatting, and refusal constraints.
- `retrieved_chunks`: List of retrieved context objects, each containing:
  - `chunk_id`: Unique section anchor (`recipe_name#section_id`).
  - `source_file`: Markdown document filename.
  - `section_title`: Section heading text.
  - `similarity_score`: Dense cosine similarity score from vector search.
  - `content`: Exact raw text chunk passed to the LLM context.
- `model_config`: Exact LLM hyperparameters (`model_name`, `temperature`, `top_p`, `max_tokens`).
- `formatted_prompt`: Fully assembled prompt string sent to the model endpoint.
- `raw_output`: Unprocessed string response returned by the LLM.
- `latency_ms`: End-to-end execution time in milliseconds.
- `refusal_triggered`: Boolean flag indicating whether the guardrail refusal phrase was emitted.

---

### B. Single Trace Replay Proof (`tr_029_5e95`)
We verified trace replayability by randomly selecting a logged trace (`seed=101`), extracting its record strictly from [`week5/traces.jsonl`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl), reconstructing the exact prompt and LLM call parameters, and executing the query without touching the vector database or application pipeline.

- **Trace ID:** `tr_029_5e95`
- **User Query:** *"What is the calorie count and carbohydrate breakdown of sourdough bread?"*
- **Prompt Version:** `v1.2.0_grounded_recipe`
- **Model Config:** `gemini-3.5-flash-lite` (Temperature: 0.0, Top-P: 0.95)
- **Retrieved Chunks Logged in Trace:**
  1. `recipe_01_sourdough#section_3` (Score: 0.7768) — *Ingredient Table*
  2. `recipe_01_sourdough#section_2` (Score: 0.7296) — *Overview*
  3. `recipe_01_sourdough#section_1` (Score: 0.7294) — *Country Sourdough Bread Title*

#### Side-by-Side Output Comparison

| Metric / Field | Original Production Run | Replayed from Trace Record | Match Status |
|:---|:---|:---|:---:|
| **Output Text** | `I cannot find information about this in the provided recipe documentation.` | `I cannot find information about this in the provided recipe documentation.` | **100% Identical** |
| **Model Endpoint** | `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | **Identical** |
| **Latency** | 1001.8 ms | 800.64 ms | Nominal |
| **Reconstruction Source** | Active live pipeline | Extracted strictly from [`traces.jsonl`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl) | **Self-Contained** |

*(Full structured verification JSON stored at [`week5/replay_evidence.json`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/replay_evidence.json)).*

---

## 2. Seeded Random Sample & 20 Open-Coded Traces

**Random Seed:** `42`  
**Sample Source:** [`week5/traces.jsonl`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl) (Pool of 57 unique production interactions)  
**Sampled Trace IDs:** `['tr_007_e7c4', 'tr_001_f31e', 'tr_018_ddf7', 'tr_034_4267', 'tr_031_b97d', 'tr_004_0cda', 'tr_024_a191', 'tr_003_7a88', 'tr_022_6965', 'tr_028_a43a', 'tr_032_9124', 'tr_002_bd95', 'tr_019_9fe7', 'tr_014_83e2', 'tr_033_0abc', 'tr_012_895b', 'tr_023_c5f5', 'tr_006_86d6', 'tr_030_aedd', 'tr_013_155c']`

### Verbatim Open-Coding Observation Table

| # | Trace ID | User Query | Verbatim Observation Sentence (What Happened) |
|:---:|:---|:---|:---|
| **1** | `tr_007_e7c4` | *How much sugar and starter tea do I need for a 1 gallon batch of kombucha?* | The model retrieved the default kombucha ingredient table (3500g water batch) and stated 250g sugar and 350g starter liquid without converting or acknowledging the user's requested 1-gallon batch size. |
| **2** | `tr_001_f31e` | *What is the exact fine sea salt weight and percentage for the country sourdough loaf?* | The model correctly retrieved the sourdough ingredient table and outputted the exact salt weight (20g) and baker's percentage (2.0%) with proper section citations. |
| **3** | `tr_018_ddf7` | *How do I burp lacto-fermented blueberry vacuum bags or mason jars?* | The system retrieved the lacto-blueberry method chunks, but outputted an upstream API 404 error message instead of an answer. |
| **4** | `tr_034_4267` | *Why is my sourdough starter not rising after day 3?* | The system retrieved sourdough method and ingredient chunks, and outputted a standard refusal string stating that starter troubleshooting advice was not found in the documentation. |
| **5** | `tr_031_b97d` | *Can you give me a quick 30 minute dinner recipe with chicken and lemon?* | The system retrieved irrelevant sourdough, kimchi, and blueberry chunks and correctly outputted a standard documentation refusal for the unindexed quick chicken recipe. |
| **6** | `tr_004_0cda` | *How much xanthan gum should I add to the gluten-free brioche dough?* | The system retrieved sourdough and miso ingredient tables lacking gluten-free brioche data, and outputted a standard refusal string. |
| **7** | `tr_024_a191` | *Is the French brioche recipe gluten-free?* | The retriever returned allergen chunks for kombucha, kimchi, and miso, and the model returned a standard documentation refusal because French brioche allergen data was not in the context. |
| **8** | `tr_003_7a88` | *How much sea salt by weight is required for making traditional red rice miso?* | The system retrieved the traditional red miso paste ingredient table (230g salt, 46.0%), but the model outputted a total refusal string because the exact query phrase "red rice miso" was not verbatim in the text. |
| **9** | `tr_022_6965` | *What fish allergen is present in traditional baechu kimchi?* | The model retrieved the classic kimchi allergen note and correctly answered that anchovy from fish sauce is the present allergen with the section citation. |
| **10** | `tr_028_a43a` | *What is the best way to ferment cabbage if I am vegan and allergic to seafood?* | The system retrieved standard kimchi method steps (which include fish sauce and shrimp paste) along with pickle allergen notes, and outputted a refusal stating no vegan seafood-free cabbage recipe was found. |
| **11** | `tr_032_9124` | *How do I fix dough that has completely overproofed and turned into soup?* | The system retrieved general sourdough method and overview chunks, and outputted a refusal because emergency overproofing remediation steps do not exist in the recipe documentation. |
| **12** | `tr_002_bd95` | *If I want to scale the country sourdough to 3 loaves, how much water and flour do I need?* | The system retrieved the single-loaf ingredient table (1000g flour, 750g water) but outputted a refusal rather than performing the 3x multiplication for the user. |
| **13** | `tr_019_9fe7` | *What is the stretch and fold schedule during sourdough bulk fermentation?* | The system retrieved the relevant sourdough method chunk describing the 4 stretch-and-folds, but outputted an upstream API 404 generation failure string. |
| **14** | `tr_014_83e2` | *What oven temperature and baking time are used for the sourdough Dutch oven bake?* | The model retrieved the sourdough baking instructions and accurately quoted 450°F (230°C) with 20 minutes covered and 22 minutes uncovered, accompanied by the correct citation. |
| **15** | `tr_033_0abc` | *What is the shelf life of opened red miso stored at room temperature?* | The system retrieved miso overview and blueberry method chunks, and outputted a refusal because post-opening room temperature shelf-life duration is not documented in the text. |
| **16** | `tr_012_895b` | *At what room temperature should red miso paste ferment and for how many months?* | The model retrieved miso fermentation steps, quoted the 6 to 12 months duration with citations, and noted that the recipe specifies "room temperature in a dark pantry" without an explicit numerical degree. |
| **17** | `tr_023_c5f5` | *Can I substitute table iodized salt for kosher salt in lacto-fermentation?* | The system retrieved overview chunks mentioning coarse salt and non-iodized salt, and returned a refusal because an explicit comparison or substitution rule for iodized table salt is not stated in the documentation. |
| **18** | `tr_006_86d6` | *What weight of salted shrimp (saeujeot) is needed for the kimchi paste?* | The model retrieved the classic kimchi ingredient table and accurately answered 25g (1.25%) with the exact section citation. |
| **19** | `tr_030_aedd` | *How do I make a chocolate lava cake with molten center?* | The retriever returned sourdough and blueberry chunks with low semantic relevance, and the system outputted a standard out-of-corpus refusal. |
| **20** | `tr_013_155c` | *What is the brine salinity percentage and fermentation time for dill pickles?* | The system retrieved all three relevant pickle documentation chunks, but outputted an upstream API 503 high-demand generation error instead of an answer. |

---

## 3. Public Benchmark Reflection (Exactly 3 Sentences)

Public benchmark leaderboards evaluate generalized reasoning on static synthetic datasets, completely hiding domain-specific failure distributions like recipe ingredient scaling failures and fermentation timing sensitivities. A single aggregate accuracy metric compresses diverse errors into a scalar score, making it impossible to distinguish between harmless refusal guardrails and critical kitchen errors that poison or ruin a dish. Conducting error analysis on production traces reveals real distribution shifts and high-severity edge cases that standardized academic benchmarks will never capture for our specific users.

---

## 4. Dated, Falsifiable Prediction

### Prediction Statement
> **On 2026-08-30, fixing 'Ignores requested batch scaling / unit conversion and outputs default single-batch weights or refuses' by implementing a deterministic Baker's Percentage scaling pre-processor in the RAG prompt will reduce its frequency from 10.0% to 0.0% - 1.0% without increasing 'Refuses practical kitchen troubleshooting, emergency fixes, and ingredient substitutions' above 30.0%.**

### Pre-Fix Commit Reference
- **Git Commit Hash:** `ee1b2840549eceafb8ba282b37b738c9838dcc51` *(Committed before code changes are implemented)*
- **Target Mode:** `Ignores requested batch scaling / unit conversion and outputs default single-batch weights or refuses` (Current Frequency: 10.0%, Severity: Ruins the dish)
- **Baseline Sample Frequency:** 2 / 20 traces (10.0%)
- **Target Post-Fix Frequency:** 0 / 20 traces (0.0%)
- **Guardrail Floor Condition:** Troubleshooting refusal mode frequency must not exceed 30.0% (currently 25.0%).
