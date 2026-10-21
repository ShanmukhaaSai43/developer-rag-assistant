# 10-Minute Demo Script: The Four-Part Standard

**System:** Pantry-to-Plate Assistant (Week 12 Capstone — Variant B)  
**Presenter:** AI Engineering Lead  
**Timing Standard:** Strictly 10 minutes (delivered to the clock)

---

## Part 1: A Real Run (0:00 – 2:45)
*Goal: Show live pantry query, visible tool calls, version citation, scaled quantities without time multiplication, and an honest refusal.*

1. **The Live Pantry & Allergy Query:**
   * *Command:* `python -m week12.main --query "I have tomatoes in the pantry and 25 minutes. Kid has a nut allergy. What can I make?"`
   * *What to highlight:*
     * Watch the visible MCP tool calls: `search_recipes` with `max_prep_and_cook_minutes=25`, followed by `check_recipe_allergens`.
     * The citation names BOTH recipe ID and version: `[rcp_quick_pasta_25m (original)]`.
2. **The Portion Scaling Demonstration:**
   * *Command:* `python -m week12.main --query "Scale the classic shortbread original recipe to 32 servings (4x). How long do I bake it?"`
   * *What to highlight:*
     * Flour scales $4\times$ ($250\text{g} \to 1000\text{g}$), butter scales ($175\text{g} \to 700\text{g}$).
     * **The Invariant Cook Time:** Point directly to the response: *"Bake time remains 25 minutes (do NOT multiply bake time to 100 minutes)."*
3. **The Honest Refusal on Safety:**
   * *Command:* `python -m week12.main --query "Can my child with a severe nut allergy eat the 2025 reformulated shortbread?"`
   * *What to highlight:*
     * The system **refuses to guess** or recommend it. It states: *"No, your child cannot eat the 2025 shortbread. `[rcp_shortbread_2025 (reformulated-2025)]` contains tree nuts (macadamia and walnut oil blend)."*

---

## Part 2: The Failures We Found (2:45 – 5:00)
*Goal: Prove failure-finding depth. (A flawless demo scores zero).*

1. **The Superseded Version Catastrophe:**
   * Show trace [`week12/logs/production.log`](file:///c:/Users/Admin/Documents/GenAi/Demo/week12/logs/production.log) where the baseline model previously cited the original nut-free shortbread for a nut-allergy query because both versions existed in the CMS.
   * Explain the fix: Allergens are exact-match structured fields, not cosine vector prose.
2. **The New Failure Mode Created by Integration:**
   * Point to [`week12/taxonomy.md`](file:///c:/Users/Admin/Documents/GenAi/Demo/week12/taxonomy.md) — *Mode 1: Allergen Re-introduction via Downstream Substitution Chain*.
   * Explain: When we integrated the agent with the test kitchen substitution tool, a user asking for dairy-free shortbread was suggested Almond Milk. While dairy-free, Almond Milk re-introduced tree nuts downstream!
3. **Top 3 Known Weaknesses Written on Wednesday Before Review:**
   * Present [`week12/weaknesses.md`](file:///c:/Users/Admin/Documents/GenAi/Demo/week12/weaknesses.md):
     1. Multi-step substitution allergen chaining.
     2. SQLite file locking at 50k queries/day.
     3. +25.0% outcome-vs-trajectory gap due to exploratory search laps on vague queries.

---

## Part 3: A Number That Moved (5:00 – 7:15)
*Goal: Quantitative before -> after proof on named metrics. Adjectives score zero.*

1. **The Named Metric:**
   * **Allergen-Unsafe Answer Rate on Reformulated 2025 Recipes:**
     * **Before (Week 4 Baseline):** 83.3% unsafe (5/6 traces failed to detect nut oil).
     * **After (Integrated System):** **0.0% unsafe** (0/6 traces unsafe — 100% safe refusal).
2. **Judge Agreement Rate on Integrated Outputs:**
   * Open [`week12/eval_report.md`](file:///c:/Users/Admin/Documents/GenAi/Demo/week12/eval_report.md).
   * Sample size: $n = 30$ cases.
   * Judge agreement rate against hand labels: **96.7%** (29/30 cases, strictly clears the >85% mandate).
3. **Explicit Statement of Non-Coverage:**
   * Read verbatim: *"Our suite does not measure home kitchen appliance calibration, user knife skills, or cross-contamination occurring on physical cutting boards outside our software boundary."*

---

## Part 4: What's Next & The 10× Plan (7:15 – 10:00)
*Goal: Closed failure loop, cost per query, and what breaks first under load.*

1. **The Closed Failure-to-Test Loop:**
   * Run live: `python -m week12.main --closed-loop`
   * Show Phase 1 RED (Almond Milk swap introduces tree nut allergen) $\to$ Phase 2 Filter $\to$ Phase 3 GREEN (Oat & coconut vegan spread approved).
2. **Cost per Query:**
   * Present [`week12/tenx_plan.md`](file:///c:/Users/Admin/Documents/GenAi/Demo/week12/tenx_plan.md).
   * Exact measured cost: **$0.000341 USD per query** (~0.034 cents).
   * At 50,000 queries/day = **$17.05 USD / day** ($511.50 / month).
3. **What Breaks First at 50,000 Queries a Day:**
   * Name the exact failure: **SQLite file-level write locking**.
   * Peak dinner traffic reaches 15–20 QPS. Concurrent telemetry logging causes `database is locked`.
   * Mitigation: Enable SQLite WAL mode immediately; migrate catalog to PostgreSQL with read replicas at 50k+ scale.
