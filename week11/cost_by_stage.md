# Cost Per Query Stage Breakdown — Week 11 Task Set B

## 1. Per-Request Cost Profile (`trace_df_8942a`)

Below is the stage-by-stage cost and resource profile extracted from production trace `trace_df_8942a`:

| Pipeline Stage | Sub-system / Operation | Latency (ms) | Tokens / Resources | Stage Cost (USD) | Percentage of Total Cost |
|---|---|---|---|---|---|
| **Retrieval** | Vector Search (ChromaDB) + Text Embedding | 115 ms | 1 Query Embedding | **$0.000050** | 11.1% |
| **Generation** | Gemini 1.5 Flash (320 in / 180 out) | 845 ms | 500 Total Tokens | **$0.000400** | 88.9% |
| **Tools** | External API / Guardrail Tools | 0 ms | None Invoked | **$0.000000** | 0.0% |
| **Total** | **End-to-End Request** | **960 ms** | **500 Tokens** | **$0.000450** | **100.0%** |

---

## 2. Stage Cost Analysis & Optimization Insights

1. **Generation Stage Dominance (88.9%)**:
   Generation accounts for **$0.000400** out of the **$0.000450** total cost. The primary cost driver is input context repetition (retrieved RAG chunks `ctx_fat_sub_014` and `ctx_ghee_notes_088` sent with system instructions).
2. **Retrieval Stage Economy (11.1%)**:
   Dense retrieval embedding calculation and local vector DB similarity lookups cost only **$0.000050** per query.
3. **Targeted Optimization Opportunity**:
   - Implementing **Prompt Caching** on static system prompts and frequent recipe RAG contexts reduces input token costs by **50%** (saving $0.00016 per query).
   - Implementing **Exact/Semantic Caching** for high-frequency queries (`dairy-free swap for butter`) eliminates generation costs completely ($0.00000 generation cost on cache hits).
