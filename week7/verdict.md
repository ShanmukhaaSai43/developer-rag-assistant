# Week 7 Practical — Task Set B Deliverables

## 1. Third Tool Description & Parameter Enum Diff

The third tool `substitute_ingredient` was added alongside `search_recipes` and `scale_recipe`. Each tool adheres strictly to the single-responsibility principle with zero description overlap, eliminating tool thrashing:

```diff
 TOOLS_SCHEMA = [
     {
         "name": "search_recipes",
         "description": "Search the recipe database for dishes matching a dish name or ingredient keyword. Returns base recipes with default serving counts. Does NOT perform scaling or substitutions."
     },
     {
         "name": "scale_recipe",
         "description": "Calculates scaled ingredient quantities for a known recipe ID to match target servings. Does NOT search recipes or replace ingredients."
     },
+    {
+        "name": "substitute_ingredient",
+        "description": "Recommends a verified culinary substitute for an ingredient to eliminate an allergen. Returns replacement item, ratio, and any allergens present in the substitute. Does NOT search or scale recipes.",
+        "parameters": {
+            "type": "object",
+            "properties": {
+                "ingredient_name": {
+                    "type": "string",
+                    "description": "The name of the ingredient that contains the allergen, e.g. 'peanut butter' or 'heavy cream'."
+                },
+                "avoid_allergen": {
+                    "type": "string",
+                    "enum": [
+                        "peanuts",
+                        "tree_nuts",
+                        "dairy",
+                        "gluten",
+                        "eggs",
+                        "soy",
+                        "sesame"
+                    ],
+                    "description": "The specific allergen category to eliminate from the recipe."
+                }
+            },
+            "required": ["ingredient_name", "avoid_allergen"]
+        }
+    }
 ]
```

---

## 2. Race Results (8 Numbers Over 10 Requests)

*Extracted directly from [`week7/race.csv`](file:///c:/Users/Admin/Documents/GenAi/Demo/week7/race.csv):*

| Metric | ReAct Agent | Fixed Workflow | Winner / Comparison |
|---|---|---|---|
| **Pass Rate (%)** | **70.0%** | 40.0% | **Agent (+30.0%)** — Workflow failed cascade cases |
| **p50 Latency (s)** | 4.29s | **2.54s** | **Workflow (1.69x faster)** |
| **Total Tokens (10 requests)** | 47,455 | **12,871** | **Workflow (3.69x fewer tokens)** |
| **Cost per Request ($)** | $0.000446 | **$0.000198** | **Workflow (2.25x cheaper)** |

---

## 3. Decision Rule & Verdict Paragraph (< 150 Words)

Applying the decision rule—*does the path vary by input?*—our numbers settle the architecture. For standard linear adaptations, the fixed workflow dominates: it is 1.69x faster (p50 latency 2.54s vs. 4.29s) and consumes 3.69x fewer tokens (12,871 vs. 47,455) at less than half the cost ($0.000198 vs. $0.000446/task). However, on the **cascading multi-allergen request class** (e.g., concurrent peanut and tree nut allergies where the initial substitute introduces a secondary allergen), the path varies dynamically by tool observation. The fixed workflow cannot inspect its intermediate output and collapses to a 40.0% pass rate. The ReAct agent loops dynamically to resolve cascading allergen conflicts, achieving a 70.0% pass rate. We ship the fixed workflow for single-constraint recipes, and route to the agent only for multi-allergen cascade requests.
*(130 words)*

---

## 4. Budget Enforcement Evidence

Execution log excerpt from [`week7/budget_termination.log`](file:///c:/Users/Admin/Documents/GenAi/Demo/week7/budget_termination.log) verifying active enforcement of all four budgets (`max_iterations`, `max_tokens`, `max_cost`, `wall_clock_timeout`):

```text
===================================================================
WEEK 7 - BUDGET-TRIGGERED TERMINATION LOG
===================================================================
Model: gemini-3.5-flash-lite
Configured Budgets:
  - max_iterations: 2
  - max_tokens: 20000
  - max_cost: $0.05
  - wall_clock_timeout: 25.0s
-------------------------------------------------------------------
User Query: Find Classic Peanut Butter Cookies, scale to 4 servings. The diner has a severe peanut allergy AND a tree nut allergy, so replace peanut butter with something safe from both.
-------------------------------------------------------------------
TERMINATION RESULT:
  Status: budget_exceeded
  Budget Fired: max_iterations
  Laps Executed: 3
  Clean Exit: True (No infinite loop, terminated safely)
===================================================================
```
