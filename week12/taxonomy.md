# Integrated Error Taxonomy — Pantry-to-Plate Assistant (Week 12)

**Domain:** Recipe Publisher & Food Safety  
**Evaluation Sample:** 30 integrated test queries running end-to-end against Agent + MCP  
**Baseline Success Rate (Week 5):** 25.0% (5/20 traces answered with exact citations)  
**Integrated Success Rate (Week 12):** 93.3% (28/30 cases cleared deterministic assertions & judge agreement)

---

## 1. Ranked Failure Modes Taxonomy (Re-scored Post-Integration)

| Rank | Failure Mode Name | Frequency (%) | Severity Level | Representative `trace_id` | Origin | User Impact |
|:---:|:---|:---:|:---:|:---:|:---:|:---|
| **1** | **Allergen Re-introduction via Downstream Substitution Chain** | **6.7%** (2/30) | **Ruins the dish / Anaphylaxis Risk** | `tr_eval_sub_01` | **NEW (Born from Integration)** | User asks to substitute cow's milk with almond milk for a baking recipe. Agent approves the dairy-free swap but fails to warn that almond milk introduces a new tree-nut allergen downstream. |
| **2** | **Extraneous Exploratory Tool Laps (Trajectory Overhead)** | **6.7%** (2/30) | **Merely annoys the cook** | `tr_eval_scale_04` | **NEW (Born from Integration)** | Agent calls `search_recipes` twice consecutively with slightly rephrased keywords before dispatching the scaling tool, inflating request latency by 1.2s. |
| **3** | **Linear Scaling of Cooking Duration (Burnt Batch Mode)** | **0.0%** (0/30) *(Mitigated)* | **Ruins the dish** | `tr_eval_scale_01` | Inherited from Week 5 | Naive LLM multiplied baking time proportionally with ingredient quantities (e.g. 4x batch = 100 min bake). Mitigated by invariant `cook_time_rule` lock in MCP scaling tool. |
| **4** | **Superseded Recipe Citation Leak Across MCP Wire** | **0.0%** (0/30) *(Mitigated)* | **Ruins the dish / Legal Risk** | `tr_eval_nut_01` | Inherited from Week 4/5 | System cited old butter-based shortbread instead of the 2025 reformulated nut-oil version. Mitigated by mandatory `[recipe_id (version)]` citation enforcement. |
| **5** | **Food Safety Minimum Temperature Omission** | **0.0%** (0/30) *(Mitigated)* | **Safety Hazard** | `tr_eval_temp_01` | Inherited from Week 5 | Poultry cooking method described as "golden and tender" without stating mandatory 74°C internal temperature. Mitigated by `get_food_safety_rule` tool prompt injection. |

---

## 2. Deep Dive: The New Mode Created by Integration

### Mode 1: Allergen Re-introduction via Downstream Substitution Chain
* **How Integration Created It:** In Week 4 (isolated RAG) and Week 7 (single-tool agent), recipe search and ingredient substitutions were tested independently. When connected into an integrated loop, the agent began chaining tools:
  $$\text{Query: Dairy-Free Shortbread} \longrightarrow \text{Tool 1: } \texttt{search\_recipes} \longrightarrow \text{Tool 2: } \texttt{substitute\_ingredient}$$
  The substitution tool suggested **Almond Milk** as a 1:1 replacement for cow's milk. While perfectly dairy-free, Almond Milk introduces **Tree Nuts**. Because the agent evaluated allergen safety before the substitution rather than *after* it, the swap re-introduced an anaphylactic allergen into a supposedly allergy-safe meal.
* **Trace ID Evidence:** `tr_eval_sub_01`
* **Mitigation:** Enforced downstream allergen inspection over the recipe *as substituted*, returning `inherent_allergens` in the MCP substitution schema.
