# Recipe Assistant Error Taxonomy (Week 5 · Task Set B)

**Domain:** Recipes & Food Fermentation  
**Evaluation Sample:** 20 seeded random production traces (`seed=42`) from [`traces.jsonl`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl)  
**Baseline Success Rate:** 25.0% (5/20 traces answered with exact weights, parameters & citations)

---

## Ranked Failure Modes Taxonomy

| Rank | Failure Mode Name | Count | Freq (%) | Severity Level | Representative `trace_id` | User Impact |
|:---:|:---|:---:|:---:|:---|:---:|:---|
| **1** | **Refuses practical kitchen troubleshooting, emergency fixes, and ingredient substitutions** | 5 | 25.0% | Merely annoys the cook | [`tr_034_4267`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl) | User receives a total refusal when asking how to fix overproofed dough, diagnose inactive starter, or substitute non-iodized salt. |
| **2** | **Out-of-corpus recipe requests triggering strict guardrail refusals** | 4 | 20.0% | Merely annoys the cook | [`tr_031_b97d`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl) | User requests recipes not in the knowledge base (e.g. quick chicken, chocolate lava cake); system correctly executes safe refusal. |
| **3** | **Upstream LLM API endpoint availability failures (404 deprecation & 503 capacity spikes)** | 3 | 15.0% | Ruins the dish | [`tr_018_ddf7`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl) | LLM endpoint deprecation (404) or server overload (503) returns raw JSON stack traces directly into recipe instructions. |
| **4** | **Ignores requested batch scaling / unit conversion and outputs default single-batch weights or refuses** | 2 | 10.0% | Ruins the dish | [`tr_007_e7c4`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl) | Cook requests 1 gallon of kombucha or 3 loaves of sourdough; assistant either refuses multiplication or serves 1-loaf quantities. |
| **5** | **Refuses near-synonym culinary queries despite retrieving matching recipe cards** | 1 | 5.0% | Merely annoys the cook | [`tr_003_7a88`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl) | Query for "traditional red rice miso" refused despite retrieving the exact Red Miso Paste (Akamiso with rice koji) card. |

---

### **Success Benchmark Baseline**
- **Successful Grounded Answers with Exact Citations:** **5 / 20 (25.0%)** — Examples: [`tr_001_f31e`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl) (20g / 2.0% salt), [`tr_022_6965`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl) (anchovy allergen), [`tr_014_83e2`](file:///c:/Users/Admin/Documents/GenAi/Demo/week5/traces.jsonl) (450°F / 20 min bake).
- **Total Sampled Traces Analyzed:** **20 / 20 (100.0%)**
