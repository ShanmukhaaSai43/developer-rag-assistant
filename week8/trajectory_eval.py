"""
===================================================================
WEEK 8 - TRAJECTORY EVALUATION ENGINE
===================================================================
Computes the 4 required trajectory numbers:
1. Tool-Choice Accuracy (%)
2. Argument Validity Rate (%) - detects "fluent fiction" against SQLite DB
3. Step Efficiency (optimal_steps / steps_taken)
4. Cost per request distribution: p50 (median) AND max, not just mean

Also computes:
- Outcome-vs-Trajectory Gap number (Outcome Pass % - Trajectory Pass %)
- Right-Answer-Wrong-Path case identification and trace extraction
- Full taxonomy classification across the Week-8 Failure Mode Zoo
===================================================================
"""

import sys
import time
import json
import statistics
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week8.dataset import BENCHMARK_CASES, evaluate_outcome
from week8.taxonomy import FailureMode, classify_run_failures
from week7.db import get_recipe_by_id, get_connection
from week7.types import AllergenType


# ===================================================================
# 1. ARGUMENT VALIDITY CHECKER (Detecting Fluent Fiction)
# ===================================================================

def validate_tool_arguments(
    tool_name: str,
    args: Dict[str, Any],
    case: Dict[str, Any]
) -> Tuple[int, int, List[str]]:
    """
    Validates tool arguments against the ground-truth SQLite database and enums.
    Returns: (valid_args_count, total_args_count, error_messages)
    """
    valid_count = 0
    total_count = 0
    errors = []

    if tool_name == "search_recipes":
        total_count += 1
        query = args.get("query")
        if query and isinstance(query, str) and len(query.strip()) > 0:
            valid_count += 1
        else:
            errors.append("search_recipes: 'query' must be a non-empty string.")

    elif tool_name == "scale_recipe":
        # Check recipe_id against real SQLite database
        total_count += 1
        recipe_id = args.get("recipe_id")
        if recipe_id and get_recipe_by_id(recipe_id) is not None:
            valid_count += 1
        else:
            errors.append(f"scale_recipe: 'recipe_id'='{recipe_id}' is fluent fiction (not in database).")

        # Check target_servings
        total_count += 1
        target_servings = args.get("target_servings")
        if isinstance(target_servings, int) and target_servings > 0:
            valid_count += 1
        else:
            errors.append(f"scale_recipe: 'target_servings'='{target_servings}' is invalid (must be > 0).")

    elif tool_name == "substitute_ingredient":
        # Check ingredient_name: must be a real ingredient in the recipe or substitutions table
        total_count += 1
        ing_name = str(args.get("ingredient_name", "")).strip().lower()

        # Connect to DB to verify ingredient existence in either recipe ingredients or substitutions
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ingredients_json FROM recipes WHERE id = ?", (case.get("recipe_id"),))
        row = cur.fetchone()
        recipe_ings = []
        if row:
            recipe_ings = [i["name"].lower() for i in json.loads(row["ingredients_json"])]

        # Also check substitutions table for intermediate swaps
        cur.execute("SELECT DISTINCT ingredient FROM substitutions")
        sub_ings = [r[0].lower() for r in cur.fetchall()]

        valid_ingredients = set(recipe_ings).union(set(sub_ings))
        # Check partial or exact match
        if any(ing_name in vi or vi in ing_name for vi in valid_ingredients if ing_name):
            valid_count += 1
        else:
            errors.append(
                f"substitute_ingredient: 'ingredient_name'='{ing_name}' is fluent fiction (not in recipe or DB)."
            )

        # Check avoid_allergen against AllergenType enum
        total_count += 1
        avoid_allergen = str(args.get("avoid_allergen", "")).strip().lower()
        valid_allergens = [a.value for a in AllergenType if a != AllergenType.NONE]
        # Common singular normalization
        singular_map = {"egg": "eggs", "peanut": "peanuts", "tree_nut": "tree_nuts", "nut": "tree_nuts"}
        normalized_allergen = singular_map.get(avoid_allergen, avoid_allergen)

        if normalized_allergen in valid_allergens:
            valid_count += 1
        else:
            errors.append(
                f"substitute_ingredient: 'avoid_allergen'='{avoid_allergen}' is invalid (must be in AllergenType)."
            )

    else:
        total_count += 1
        errors.append(f"Unknown tool '{tool_name}' invoked.")

    return valid_count, total_count, errors


# ===================================================================
# 2. EVALUATION SUITE RUNNER
# ===================================================================

def evaluate_run(case: Dict[str, Any], run_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates a single execution trajectory against expected tool sequences,
    argument validity, step efficiency, and outcome correctness.
    """
    tool_sequence = tuple(run_result.get("tool_sequence", []))
    trajectory_steps = run_result.get("trajectory_steps", [])

    # 1. Trajectory Sequence Check against valid alternate paths set
    valid_sequences = case["valid_tool_sequences"]
    trajectory_passed = tool_sequence in valid_sequences

    # 2. Tool-Choice Accuracy
    # Count how many tool choices were valid given task constraints
    valid_tools_in_case = {"search_recipes", "scale_recipe", "substitute_ingredient"}
    correct_choices = 0
    for t in tool_sequence:
        if t in valid_tools_in_case:
            correct_choices += 1
    tool_choice_accuracy = (correct_choices / len(tool_sequence)) if tool_sequence else 0.0

    # 3. Argument Validity Rate
    total_valid_args = 0
    total_checked_args = 0
    all_arg_errors = []
    for s in trajectory_steps:
        t_name = s.get("tool_name", "")
        t_args = s.get("arguments", {})
        v_count, c_count, errs = validate_tool_arguments(t_name, t_args, case)
        total_valid_args += v_count
        total_checked_args += c_count
        all_arg_errors.extend(errs)

    arg_validity_rate = (total_valid_args / total_checked_args) if total_checked_args > 0 else 0.0

    # 4. Step Efficiency: optimal_steps / steps_taken
    actual_steps = len(tool_sequence)
    optimal_steps = case["optimal_steps"]
    step_efficiency = (optimal_steps / actual_steps) if actual_steps > 0 else 0.0
    # Also ratio steps taken / steps needed as noted in requirement phrasing
    steps_taken_over_needed = (actual_steps / optimal_steps) if optimal_steps > 0 else 0.0

    # 5. Outcome Evaluation
    outcome_res = evaluate_outcome(case, run_result.get("final_recipe"))
    outcome_passed = outcome_res["passed"]

    # 6. Failure Taxonomy Classification
    failure_modes = classify_run_failures(case, run_result, all_arg_errors, trajectory_passed)

    # 7. Right-Answer-Wrong-Path Detection
    is_right_answer_wrong_path = outcome_passed and (not trajectory_passed)

    return {
        "case_id": case["id"],
        "type": case["type"],
        "query": case["query"],
        "tool_sequence": list(tool_sequence),
        "trajectory_passed": trajectory_passed,
        "outcome_passed": outcome_passed,
        "is_right_answer_wrong_path": is_right_answer_wrong_path,
        "tool_choice_accuracy": tool_choice_accuracy,
        "argument_validity_rate": arg_validity_rate,
        "optimal_steps": optimal_steps,
        "actual_steps": actual_steps,
        "step_efficiency": round(step_efficiency, 4),
        "steps_taken_over_needed": round(steps_taken_over_needed, 4),
        "tokens": run_result.get("total_tokens", 0),
        "cost_usd": run_result.get("total_cost_usd", 0.0),
        "latency_s": run_result.get("latency_seconds", 0.0),
        "argument_errors": all_arg_errors,
        "outcome_errors": outcome_res.get("errors", []),
        "failure_modes": [m.value for m in failure_modes]
    }


def summarize_evaluation(eval_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes overall summary statistics across all evaluated cases.
    """
    n = len(eval_records)
    if n == 0:
        return {}

    outcome_passes = sum(1 for r in eval_records if r["outcome_passed"])
    trajectory_passes = sum(1 for r in eval_records if r["trajectory_passed"])

    outcome_pass_rate = (outcome_passes / n) * 100.0
    trajectory_pass_rate = (trajectory_passes / n) * 100.0
    gap = outcome_pass_rate - trajectory_pass_rate

    avg_tool_choice_acc = statistics.mean([r["tool_choice_accuracy"] for r in eval_records]) * 100.0
    avg_arg_validity_rate = statistics.mean([r["argument_validity_rate"] for r in eval_records]) * 100.0
    avg_step_efficiency = statistics.mean([r["step_efficiency"] for r in eval_records])

    costs = [r["cost_usd"] for r in eval_records]
    cost_mean = statistics.mean(costs)
    cost_p50 = statistics.median(costs)
    cost_max = max(costs)
    cost_min = min(costs)

    latencies = [r["latency_s"] for r in eval_records]
    latency_mean = statistics.mean(latencies)
    latency_p50 = statistics.median(latencies)
    latency_max = max(latencies)

    # Count failure modes across all runs
    mode_counts: Dict[str, int] = {}
    for r in eval_records:
        for mode in r["failure_modes"]:
            if mode != FailureMode.FM_NONE.value:
                mode_counts[mode] = mode_counts.get(mode, 0) + 1

    # Find right-answer-wrong-path cases
    gap_cases = [r for r in eval_records if r["is_right_answer_wrong_path"]]

    return {
        "total_cases": n,
        "outcome_pass_rate": round(outcome_pass_rate, 1),
        "trajectory_pass_rate": round(trajectory_pass_rate, 1),
        "outcome_vs_trajectory_gap": round(gap, 1),
        "avg_tool_choice_accuracy": round(avg_tool_choice_acc, 1),
        "avg_argument_validity_rate": round(avg_arg_validity_rate, 1),
        "avg_step_efficiency": round(avg_step_efficiency, 3),
        "cost_usd": {
            "mean": round(cost_mean, 6),
            "p50": round(cost_p50, 6),
            "max": round(cost_max, 6),
            "min": round(cost_min, 6)
        },
        "latency_s": {
            "mean": round(latency_mean, 2),
            "p50": round(latency_p50, 2),
            "max": round(latency_max, 2)
        },
        "mode_counts": mode_counts,
        "right_answer_wrong_path_cases": gap_cases
    }


if __name__ == "__main__":
    print("=== TRAJECTORY EVALUATOR LOADED SUCCESSFULLY ===")
