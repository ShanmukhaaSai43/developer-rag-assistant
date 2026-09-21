"""
===================================================================
WEEK 8 - STEP 2: BASELINE TRAJECTORY EVALUATION RUNNER
===================================================================
Executes the baseline Recipe ReAct Agent across all 10 benchmark cases.
Computes and reports:
1. The 4 required trajectory numbers:
   - Tool-choice accuracy
   - Argument validity rate (fluent fiction check)
   - Step efficiency
   - Cost per request (reported with p50 AND max!)
2. Outcome-vs-Trajectory Gap number (Outcome Pass % - Trajectory Pass %)
3. Right-Answer-Wrong-Path case analysis with full trajectory trace
4. Week-8 Failure Mode taxonomy ranking and top mode identification
===================================================================
"""

import sys
import time
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from week8.agent import RecipeReActAgent
from week8.dataset import BENCHMARK_CASES
from week8.trajectory_eval import evaluate_run, summarize_evaluation


def run_baseline_evaluation():
    print("=" * 80)
    print("WEEK 8 STEP 2: BASELINE TRAJECTORY EVALUATION (10 RECIPE BENCHMARK CASES)")
    print("=" * 80 + "\n")

    agent = RecipeReActAgent(max_iterations=8, wall_clock_timeout=35.0)

    eval_results = []
    raw_runs = []

    for idx, case in enumerate(BENCHMARK_CASES, start=1):
        case_id = case["id"]
        case_type = case["type"]
        query = case["query"]

        print(f"[{idx}/10] Testing {case_id} ({case_type.upper()}): {query[:65]}...")

        run_output = agent.run(query)
        eval_record = evaluate_run(case, run_output)

        eval_results.append(eval_record)
        raw_runs.append({
            "case": case,
            "run_output": run_output,
            "eval_record": eval_record
        })

        t_pass = "[PASS]" if eval_record["trajectory_passed"] else "[FAIL]"
        o_pass = "[PASS]" if eval_record["outcome_passed"] else "[FAIL]"
        print(f"       -> Trajectory: {t_pass} | Outcome: {o_pass} | Steps: {eval_record['actual_steps']}/{eval_record['optimal_steps']}")
        print(f"       -> Tools: {eval_record['tool_sequence']}")
        if eval_record["is_right_answer_wrong_path"]:
            print("       *** [!] GAP DETECTED: Right Answer reached via Wrong Path! ***")
        if eval_record["argument_errors"]:
            for err in eval_record["argument_errors"]:
                print(f"       *** [!] ARGUMENT FICTION: {err} ***")

        # Brief rate limit buffer
        time.sleep(2.0)

    # Save complete raw run artifacts
    traces_path = Path(__file__).resolve().parent / "baseline_traces.json"
    # Filter out non-serializable objects (like sets) in case
    serializable_runs = []
    for r in raw_runs:
        c_copy = dict(r["case"])
        c_copy["valid_tool_sequences"] = [list(seq) for seq in c_copy["valid_tool_sequences"]]
        serializable_runs.append({
            "case": c_copy,
            "run_output": r["run_output"],
            "eval_record": r["eval_record"]
        })

    with open(traces_path, "w", encoding="utf-8") as f:
        json.dump(serializable_runs, f, indent=2)
    print(f"\n[Saved full baseline traces to {traces_path}]")

    # Compute and display summary statistics
    summary = summarize_evaluation(eval_results)

    print("\n" + "=" * 80)
    print("BASELINE TRAJECTORY EVALUATION REPORT")
    print("=" * 80)
    print(f"Total Benchmark Cases:           {summary['total_cases']}")
    print(f"Outcome Pass Rate:               {summary['outcome_pass_rate']}%")
    print(f"Trajectory Pass Rate:            {summary['trajectory_pass_rate']}%")
    print(f"-> OUTCOME-VS-TRAJECTORY GAP:    {summary['outcome_vs_trajectory_gap']}%")
    print("-" * 80)
    print("THE FOUR TRAJECTORY METRICS:")
    print(f"1. Tool-Choice Accuracy:         {summary['avg_tool_choice_accuracy']}%")
    print(f"2. Argument Validity Rate:       {summary['avg_argument_validity_rate']}%")
    print(f"3. Step Efficiency (optimal/act):{summary['avg_step_efficiency']}")
    print("4. Cost per Request (USD):")
    print(f"   - p50 (Median):               ${summary['cost_usd']['p50']:.6f}")
    print(f"   - Max:                        ${summary['cost_usd']['max']:.6f}")
    print(f"   - Mean:                       ${summary['cost_usd']['mean']:.6f}")
    print(f"   - Min:                        ${summary['cost_usd']['min']:.6f}")
    print("-" * 80)
    print("FAILURE MODE TAXONOMY BREAKDOWN (WEEK 8 ZOO):")
    if summary["mode_counts"]:
        sorted_modes = sorted(summary["mode_counts"].items(), key=lambda x: x[1], reverse=True)
        for rank, (mode_name, count) in enumerate(sorted_modes, start=1):
            print(f"   Rank {rank}: {mode_name} -> {count} occurrences")
        print(f"\n-> #1 TOP FAILURE MODE: {sorted_modes[0][0]} ({sorted_modes[0][1]} cases)")
    else:
        print("   No failure modes detected.")

    print("-" * 80)
    print("RIGHT-ANSWER-WRONG-PATH TRACE ANALYSIS:")
    gap_cases = summary["right_answer_wrong_path_cases"]
    if gap_cases:
        for gc in gap_cases:
            print(f"\nCase ID: {gc['case_id']} ({gc['type'].upper()})")
            print(f"Query:   \"{gc['query']}\"")
            print(f"Outcome: PASSED (Recipe ingredients/servings correctly satisfied user request)")
            print(f"Trajectory: FAILED")
            print(f"Wrong Path Taken: {gc['tool_sequence']}")
            print(f"Argument Errors: {gc['argument_errors']}")
            print(f"Failure Modes:   {gc['failure_modes']}")
    else:
        print("No right-answer-wrong-path instances detected in this run.")

    print("=" * 80 + "\n")
    return summary, raw_runs


if __name__ == "__main__":
    run_baseline_evaluation()
