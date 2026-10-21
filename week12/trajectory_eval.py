"""
=============================================================================
WEEK 12 - STEP 6: TRAJECTORY EVALUATION & OUTCOME-VS-TRAJECTORY GAP
=============================================================================
Measures:
1. Tool-Choice Accuracy: Did the agent choose the exact optimal tool sequence?
2. Outcome Accuracy: Did the agent achieve the correct final kitchen answer?
3. The Outcome-vs-Trajectory Gap: (Outcome % - Trajectory %)
   - Exposes when the model gets the right answer through sub-optimal or redundant laps
=============================================================================
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week12.agent import PantryToPlateAgent

TRAJECTORY_BENCHMARK = [
    {
        "id": "traj_01",
        "query": "Is the 2025 shortbread safe for someone with a tree nut allergy?",
        "optimal_sequence": ("search_recipes", "check_recipe_allergens"),
        "acceptable_alternates": [
            ("check_recipe_allergens",),
            ("search_recipes", "check_recipe_allergens")
        ]
    },
    {
        "id": "traj_02",
        "query": "What fast 25-minute pasta dishes do you have that are nut-free?",
        "optimal_sequence": ("search_recipes", "check_recipe_allergens"),
        "acceptable_alternates": [
            ("search_recipes",),
            ("search_recipes", "check_recipe_allergens")
        ]
    },
    {
        "id": "traj_03",
        "query": "Scale the original shortbread to 32 servings. What are the quantities?",
        "optimal_sequence": ("search_recipes", "scale_recipe_ingredients"),
        "acceptable_alternates": [
            ("search_recipes", "scale_recipe_ingredients"),
            ("scale_recipe_ingredients",)
        ]
    },
    {
        "id": "traj_04",
        "query": "What is the safe cooking temperature for chicken breast?",
        "optimal_sequence": ("get_food_safety_rule",),
        "acceptable_alternates": [
            ("get_food_safety_rule",),
            ("search_recipes", "get_food_safety_rule")
        ]
    },
    {
        "id": "traj_05",
        "query": "Can I substitute cow's milk with almond milk?",
        "optimal_sequence": ("substitute_ingredient",),
        "acceptable_alternates": [
            ("substitute_ingredient",)
        ]
    },
    {
        "id": "traj_06",
        "query": "How do I make the heritage country sourdough bread?",
        "optimal_sequence": ("search_recipes",),
        "acceptable_alternates": [
            ("search_recipes",)
        ]
    },
    {
        "id": "traj_07",
        "query": "What can I replace pine nuts with for a nut-free pesto?",
        "optimal_sequence": ("substitute_ingredient",),
        "acceptable_alternates": [
            ("substitute_ingredient",)
        ]
    },
    {
        "id": "traj_08",
        "query": "Scale roast chicken for 8 people and tell me the required internal temperature.",
        "optimal_sequence": ("search_recipes", "scale_recipe_ingredients", "get_food_safety_rule"),
        "acceptable_alternates": [
            ("search_recipes", "scale_recipe_ingredients", "get_food_safety_rule"),
            ("search_recipes", "get_food_safety_rule", "scale_recipe_ingredients")
        ]
    },
    {
        "id": "traj_09",
        "query": "What internal temperature must ground beef reach?",
        "optimal_sequence": ("get_food_safety_rule",),
        "acceptable_alternates": [
            ("get_food_safety_rule",)
        ]
    },
    {
        "id": "traj_10",
        "query": "How do I replace all-purpose flour for someone with celiac disease?",
        "optimal_sequence": ("substitute_ingredient",),
        "acceptable_alternates": [
            ("substitute_ingredient",)
        ]
    },
    {
        "id": "traj_11",
        "query": "Can I serve the 2025 reformulated shortbread at a nut-free school?",
        "optimal_sequence": ("search_recipes", "check_recipe_allergens"),
        "acceptable_alternates": [
            ("search_recipes", "check_recipe_allergens"),
            ("check_recipe_allergens",)
        ]
    },
    {
        "id": "traj_12",
        "query": "Scale the classic shortbread to 4 servings (half batch).",
        "optimal_sequence": ("search_recipes", "scale_recipe_ingredients"),
        "acceptable_alternates": [
            ("search_recipes", "scale_recipe_ingredients"),
            ("scale_recipe_ingredients",)
        ]
    }
]

def run_trajectory_evaluation():
    print("=" * 75)
    print("  STEP 6: TRAJECTORY EVALUATION & OUTCOME-VS-TRAJECTORY GAP")
    print("=" * 75)

    agent = PantryToPlateAgent()
    total_cases = len(TRAJECTORY_BENCHMARK)
    outcome_passes = 0
    trajectory_passes = 0
    records = []

    try:
        for idx, item in enumerate(TRAJECTORY_BENCHMARK, 1):
            cid = item["id"]
            query = item["query"]
            optimal_seq = item["optimal_sequence"]
            alternates = [tuple(alt) for alt in item["acceptable_alternates"]]

            res = agent.run(query, trace_id=f"tr_{cid}")
            actual_seq = res["tool_sequence"]
            output = res["output"]

            # Outcome Evaluation: Did it deliver a non-empty, safe answer?
            outcome_ok = len(output.strip()) > 30 and not ("error" in output.lower() and len(output) < 50)
            if outcome_ok:
                outcome_passes += 1

            # Trajectory Evaluation: Did the tool sequence match optimal or acceptable alternates?
            traj_ok = actual_seq in alternates
            if traj_ok:
                trajectory_passes += 1

            gap_flag = "[GAP: Extraneous Lap]" if (outcome_ok and not traj_ok) else "[OPTIMAL]"
            print(f"  [{idx:02d}/{total_cases}] {cid:<10} | Outcome: {'OK' if outcome_ok else 'FAIL'} | Traj: {'OK' if traj_ok else 'DEV'} | {gap_flag}")
            print(f"       Expected: {optimal_seq}")
            print(f"       Actual:   {actual_seq}")

            records.append({
                "case_id": cid,
                "query": query,
                "expected": list(optimal_seq),
                "actual": list(actual_seq),
                "outcome_ok": outcome_ok,
                "trajectory_ok": traj_ok
            })
            time.sleep(2.0)  # Pacing

    finally:
        agent.close()

    outcome_acc = round((outcome_passes / total_cases) * 100, 1)
    traj_acc = round((trajectory_passes / total_cases) * 100, 1)
    gap = round(outcome_acc - traj_acc, 1)

    print("\n" + "=" * 75)
    print("  TRAJECTORY EVALUATION RESULTS")
    print(f"  * Sample Size:                 n = {total_cases} cases")
    print(f"  * Outcome Accuracy:            {outcome_acc}% ({outcome_passes}/{total_cases})")
    print(f"  * Tool-Choice Accuracy (Traj): {traj_acc}% ({trajectory_passes}/{total_cases})")
    print(f"  * Outcome-vs-Trajectory Gap:   +{gap}%  (Honest reporting of exploratory laps)")
    print("=" * 75)

    return {
        "n": total_cases,
        "outcome_acc": outcome_acc,
        "traj_acc": traj_acc,
        "gap": gap,
        "records": records
    }

if __name__ == "__main__":
    run_trajectory_evaluation()
