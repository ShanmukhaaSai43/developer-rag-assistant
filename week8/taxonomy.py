"""
===================================================================
WEEK 8 - FAILURE MODE TAXONOMY ZOO
===================================================================
Defines the failure mode taxonomy for the Recipe ReAct Agent
as taught in Week 8 Module 4 (Agent Failure Modes & Trajectory Evals).

Taxonomy Modes:
1. FM_SHORTCUT: Missing Tool Call / Shortcut Hallucination
   (Agent guesses substitution or proportions from internal weights without tool query)
2. FM_FLUENT_FICTION: Argument Hallucination / Fluent Fiction
   (Agent passes fabricated recipe_id, non-existent ingredient, or invalid allergen enum)
3. FM_LOOP: Redundant Tool Loops / Thrashing
   (Agent calls the same tool repeatedly with identical or thrashing arguments)
4. FM_ORDER: Out-of-Order Execution
   (Agent attempts scaling or substitution before searching or verifying recipe)
5. FM_BUDGET_GIVEUP: Budget Exceeded / Silent Abandonment
   (Hit iteration limit, token limit, or wall-clock timeout)
===================================================================
"""

from enum import Enum
from typing import Dict, Any, List, Optional


class FailureMode(str, Enum):
    FM_SHORTCUT = "Missing Tool Call / Shortcut Hallucination"
    FM_FLUENT_FICTION = "Argument Hallucination / Fluent Fiction"
    FM_LOOP = "Redundant Tool Loops / Thrashing"
    FM_ORDER = "Out-of-Order Execution"
    FM_BUDGET_GIVEUP = "Budget Exceeded / Silent Abandonment"
    FM_NONE = "No Failure (Clean Execution)"


FAILURE_MODE_DESCRIPTIONS = {
    FailureMode.FM_SHORTCUT: (
        "The agent outputs a final answer or substitution without ever invoking the "
        "required tool (e.g. producing a nut-free replacement without calling substitute_ingredient)."
    ),
    FailureMode.FM_FLUENT_FICTION: (
        "The agent hallucinates tool arguments (e.g. inventing a fake recipe_id like "
        "'fettuccine_alfredo_01' instead of 'rec_creamy_alfredo', or a non-existent allergen name)."
    ),
    FailureMode.FM_LOOP: (
        "The agent enters a redundant loop or thrashing cycle, repeatedly querying the "
        "same tool with unchanged or oscillating arguments."
    ),
    FailureMode.FM_ORDER: (
        "The agent calls tools in an invalid chronological order (e.g. scaling or substituting "
        "before performing the initial recipe search)."
    ),
    FailureMode.FM_BUDGET_GIVEUP: (
        "The agent runs out of allotted iterations, tokens, or wall-clock time and terminates "
        "without completing the user request."
    )
}


def classify_run_failures(
    case: Dict[str, Any],
    run_result: Dict[str, Any],
    arg_validation_errors: List[str],
    trajectory_passed: bool
) -> List[FailureMode]:
    """
    Classifies an agent execution run into one or more taxonomy failure modes.
    """
    detected_modes: List[FailureMode] = []
    tool_sequence = run_result.get("tool_sequence", [])
    status = run_result.get("status")

    # 1. Check Budget / Abandonment
    if status == "budget_exceeded":
        detected_modes.append(FailureMode.FM_BUDGET_GIVEUP)

    # 2. Check Out-of-Order Execution
    # First tool call must be search_recipes
    if tool_sequence and tool_sequence[0] != "search_recipes":
        detected_modes.append(FailureMode.FM_ORDER)

    # 3. Check Argument Hallucination / Fluent Fiction
    if arg_validation_errors:
        detected_modes.append(FailureMode.FM_FLUENT_FICTION)

    # 4. Check Redundant Tool Loops / Thrashing
    # If same tool is called back-to-back with identical arguments or exceeding 2x optimal steps
    steps = run_result.get("trajectory_steps", [])
    seen_calls = set()
    has_loop = False
    for s in steps:
        call_key = (s.get("tool_name"), str(sorted(s.get("arguments", {}).items())))
        if call_key in seen_calls:
            has_loop = True
            break
        seen_calls.add(call_key)
    if has_loop or len(tool_sequence) > (case.get("optimal_steps", 3) + 2):
        detected_modes.append(FailureMode.FM_LOOP)

    # 5. Check Shortcut Hallucination / Missing Tool Call
    # Required substitute_ingredient was skipped, yet agent gave a response
    needed_sub_calls = 2 if case["type"] == "cascade" else 1
    actual_sub_calls = tool_sequence.count("substitute_ingredient")
    actual_scale_calls = tool_sequence.count("scale_recipe")
    if actual_sub_calls < needed_sub_calls or actual_scale_calls < 1:
        detected_modes.append(FailureMode.FM_SHORTCUT)

    if not detected_modes and trajectory_passed:
        return [FailureMode.FM_NONE]

    return detected_modes
