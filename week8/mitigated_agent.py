"""
===================================================================
WEEK 8 - STEP 3: MITIGATED ReAct RECIPE AGENT
===================================================================
Applies EXACTLY ONE mitigation to close the #1 failure mode identified
in Step 2: `Budget Exceeded / Silent Abandonment` (driven by multi-tool
parallel thrashing and redundant substitution loops in cascading cases).

THE SINGLE MITIGATION: Tighter Tool Description (Tool Contract Tightening)
-------------------------------------------------------------------
We sharpen the tool contract on `substitute_ingredient` to strictly restrict
tool calls to ONE explicit target ingredient at a time, forbidding speculative
batch substitutions and instructing sequential inspection for cascading swaps.

DIFF APPLIED:
```diff
- "description": "Recommends a verified culinary substitute for an ingredient to eliminate an allergen. Returns replacement item, ratio, and any allergens present in the substitute. Does NOT search or scale recipes."
+ "description": "Recommends a verified culinary substitute for ONE specific target ingredient to eliminate an allergen. Strictly query ONE ingredient per step matching the user's explicit substitution request. For cascading multi-allergen swaps, inspect the returned replacement item before querying a second substitution. Never execute parallel or speculative substitutions on unrequested ingredients. Does NOT search or scale recipes."
```
===================================================================
"""

import sys
import copy
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week8.agent import RecipeReActAgent, DEFAULT_MODEL
from week7.tools import TOOLS_SCHEMA

# ===================================================================
# THE SINGLE MITIGATION: TIGHTENED TOOL SCHEMA
# ===================================================================

MITIGATED_TOOLS_SCHEMA: List[Dict[str, Any]] = copy.deepcopy(TOOLS_SCHEMA)

# Apply the single description tightening to substitute_ingredient
for tool in MITIGATED_TOOLS_SCHEMA:
    if tool["name"] == "substitute_ingredient":
        tool["description"] = (
            "Recommends a verified culinary substitute for ONE specific target ingredient to "
            "eliminate an allergen. Strictly query ONE ingredient per step matching the user's "
            "explicit substitution request. For cascading multi-allergen swaps, inspect the returned "
            "replacement item before querying a second substitution. Never execute parallel or "
            "speculative substitutions on unrequested ingredients. Does NOT search or scale recipes."
        )


class MitigatedRecipeAgent(RecipeReActAgent):
    """
    Recipe ReAct Agent with the single tool description mitigation applied.
    All budgets, models, temperatures, and execution logic remain strictly identical.
    """
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        max_iterations: int = 8,
        max_tokens: int = 25_000,
        max_cost: float = 0.05,
        wall_clock_timeout: float = 35.0
    ):
        super().__init__(
            model_name=model_name,
            max_iterations=max_iterations,
            max_tokens=max_tokens,
            max_cost=max_cost,
            wall_clock_timeout=wall_clock_timeout,
            tools_schema=MITIGATED_TOOLS_SCHEMA
        )


if __name__ == "__main__":
    print("=== MITIGATED AGENT LOADED SUCCESSFULLY ===")
    print("Single Mitigation Applied: Tighter Tool Description for `substitute_ingredient`")
    for t in MITIGATED_TOOLS_SCHEMA:
        if t["name"] == "substitute_ingredient":
            print(f"\nTightened Description:\n\"{t['description']}\"\n")
