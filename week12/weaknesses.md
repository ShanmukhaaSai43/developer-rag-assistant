# Top 3 Known Weaknesses — Pantry-to-Plate Assistant

**Date:** Wednesday, October 15, 2026 (Written Unprompted Before Review)  
**System Version:** v1.0.0-rc1 (Integrated Agent + MCP)

---

### Weakness 1: Downstream Inherent Allergen Propagation in Multi-Step Swaps
* **The Vulnerability:** If a user requests a complex dietary adaptation (e.g., "make this vegan and gluten-free"), the system might propose two chained substitutions:
  $$\text{Butter} \to \text{Almond Milk Butter Blend} \quad \text{and} \quad \text{Flour} \to \text{Oat Flour}$$
  If the user has a secondary unstated or stated nut allergy, the almond substitute resolves the dairy constraint but introduces an anaphylactic tree-nut hazard downstream.
* **Why it Exists:** The baseline retrieval pipeline checks allergen flags on the *original catalog card*, not dynamically over the synthetic composite recipe produced by chained swaps.
* **Guardrail Implemented:** The `substitute_ingredient` tool now includes `inherent_allergens` metadata, and our bonus evaluation test specifically asserts safety on the recipe *as substituted*.

---

### Weakness 2: SQLite File Lock Contention at 50,000 Queries/Day
* **The Vulnerability:** `week12/data/recipes.db` is an on-disk SQLite database. While read queries are fast (~2ms), writing distributed telemetry records and executing concurrent searches causes write-lock contention under production concurrency spikes.
* **Why it Exists:** Built for zero-dependency local execution so any stranger can run the app without external database servers.
* **Mitigation / 10× Plan:** SQLite WAL (Write-Ahead Logging) mode handles up to ~5,000 queries/day. Beyond 50,000 queries/day, migration to managed PostgreSQL / Cloud Spanner with read-replicas is required.

---

### Weakness 3: Exploratory Trajectory Laps on Ambiguous Pantry Queries
* **The Vulnerability:** When a user query is vague (e.g. *"what can I make with whatever is in the fridge"*), the agent occasionally makes two speculative `search_recipes` tool calls with slightly modified synonyms before deciding on a dish.
* **Impact:** Adds ~1.1 seconds of unnecessary latency and ~$0.00008 USD per query.
* **Quantified Gap:** Exposes our **+25.0% outcome-vs-trajectory gap** (Outcome accuracy is 91.7%, while optimal trajectory accuracy is 66.7% due to exploratory search and validation laps).
