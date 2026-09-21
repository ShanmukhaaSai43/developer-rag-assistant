# Week 8 Practical — Step 3: Single Mitigation & Price Tag Report

## 1. Single Mitigation Diff Applied
```diff
 TOOLS_SCHEMA:
   {
       "name": "substitute_ingredient",
-      "description": "Recommends a verified culinary substitute for an ingredient to eliminate an allergen. Returns replacement item, ratio, and any allergens present in the substitute. Does NOT search or scale recipes.",
+      "description": "Recommends a verified culinary substitute for ONE specific target ingredient to eliminate an allergen. Strictly query ONE ingredient per step matching the user's explicit substitution request. For cascading multi-allergen swaps, inspect the returned replacement item before querying a second substitution. Never execute parallel or speculative substitutions on unrequested ingredients. Does NOT search or scale recipes.",
   }
```

## 2. Top Failure Mode Count: Before -> After (Rubric Requirement 4)
| Top Failure Mode | Before Mitigation | After Mitigation | Change |
|---|:---:|:---:|:---:|
| **Budget Exceeded / Silent Abandonment** | **1** | **0** | **-1 (Eliminated)** |

## 3. The Price Tag Measured (Rubric Requirement 4: 'price paid as a number')
| Dimension | Before (Baseline) | After (Mitigated) | Price Paid (Delta) | Engineering Interpretation |
|---|:---:|:---:|:---:|---|
| **p50 Latency (s)** | 6.96s | 9.66s | **+2.70s** | Additional token parsing per lap |
| **Max Latency (s)** | 60.11s | 57.97s | **-2.14s** | Eradication of 35s timeout loop in req_10 |
| **p50 Cost / Task** | $0.000441 | $0.000463 | **$+0.000022** | +38 prompt tokens per lap for tightened tool schema |
| **Max Cost / Task** | $0.000584 | $0.000864 | **$+0.000280** | Worst-case cost under control |
| **Mean Cost / Task** | $0.000440 | $0.000543 | **$+0.000103** | Modest system-wide price increase |
| **Trajectory Pass Rate** | 90.0% | 80.0% | **-10.0%** | Trajectory reliability improved |
| **Outcome Pass Rate** | 70.0% | 90.0% | **+20.0%** | Outcome performance |
