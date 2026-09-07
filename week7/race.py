"""
===================================================================
WEEK 7 - STEP 6: HEAD-TO-HEAD RACE (Agent vs. Fixed Workflow)
===================================================================
Races the ReAct Agent against the Fixed Workflow across all 10 requests.
Calculates the 4 required numbers for both systems (8 numbers total):
1. Pass Rate (%)
2. p50 Latency (median seconds)
3. Total Tokens (summed across all laps/steps)
4. Cost per Request (USD)

Saves results to:
- `week7/race.csv`: The official 8-number comparison table
- `week7/race_details.csv`: Per-request breakdown
===================================================================
"""

import sys
import time
import csv
import statistics
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from week7.agent import RecipeReActAgent
from week7.workflow import RecipeFixedWorkflow
from week7.dataset import BENCHMARK_REQUESTS, evaluate_recipe

def run_race():
    print("=" * 70)
    print("WEEK 7 HEAD-TO-HEAD RACE: AGENT vs. FIXED WORKFLOW (10 REQUESTS)")
    print("=" * 70 + "\n")

    agent = RecipeReActAgent(max_iterations=8, wall_clock_timeout=35.0)
    workflow = RecipeFixedWorkflow()

    race_records = []

    agent_passes = []
    agent_latencies = []
    agent_tokens = []
    agent_costs = []

    wf_passes = []
    wf_latencies = []
    wf_tokens = []
    wf_costs = []

    for idx, case in enumerate(BENCHMARK_REQUESTS, start=1):
        req_id = case["id"]
        req_type = case["type"]
        query = case["query"]

        print(f"[{idx}/10] Testing {req_id} ({req_type.upper()}): {query[:60]}...")

        # 1. RUN AGENT
        print("  -> Running ReAct Agent...", end="", flush=True)
        agent_res = agent.run(query)
        agent_eval = evaluate_recipe(case, agent_res.get("final_recipe"))
        passed_agent = agent_eval["passed"]

        agent_passes.append(1 if passed_agent else 0)
        agent_latencies.append(agent_res["latency_seconds"])
        agent_tokens.append(agent_res["total_tokens"])
        agent_costs.append(agent_res["total_cost_usd"])
        print(f" Done ({agent_res['latency_seconds']}s, {agent_res['total_tokens']} tokens, Pass={passed_agent})")

        # Brief rate limit pause
        time.sleep(2.5)

        # 2. RUN WORKFLOW
        print("  -> Running Fixed Workflow...", end="", flush=True)
        wf_res = workflow.run(query)
        wf_eval = evaluate_recipe(case, wf_res.get("final_recipe"))
        passed_wf = wf_eval["passed"]

        wf_passes.append(1 if passed_wf else 0)
        wf_latencies.append(wf_res["latency_seconds"])
        wf_tokens.append(wf_res["total_tokens"])
        wf_costs.append(wf_res["total_cost_usd"])
        print(f" Done ({wf_res['latency_seconds']}s, {wf_res['total_tokens']} tokens, Pass={passed_wf})")

        race_records.append({
            "request_id": req_id,
            "type": req_type,
            "query": query,
            "agent_pass": passed_agent,
            "agent_latency_s": agent_res["latency_seconds"],
            "agent_tokens": agent_res["total_tokens"],
            "agent_cost_usd": agent_res["total_cost_usd"],
            "wf_pass": passed_wf,
            "wf_latency_s": wf_res["latency_seconds"],
            "wf_tokens": wf_res["total_tokens"],
            "wf_cost_usd": wf_res["total_cost_usd"],
        })

        time.sleep(2.5)

    # Calculate the 8 numbers
    total_cases = len(BENCHMARK_REQUESTS)
    agent_pass_rate = (sum(agent_passes) / total_cases) * 100.0
    agent_p50_latency = statistics.median(agent_latencies)
    agent_total_tokens = sum(agent_tokens)
    agent_avg_cost = sum(agent_costs) / total_cases

    wf_pass_rate = (sum(wf_passes) / total_cases) * 100.0
    wf_p50_latency = statistics.median(wf_latencies)
    wf_total_tokens = sum(wf_tokens)
    wf_avg_cost = sum(wf_costs) / total_cases

    # Save race_details.csv
    details_file = ROOT_DIR / "week7" / "race_details.csv"
    with open(details_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=race_records[0].keys())
        writer.writeheader()
        writer.writerows(race_records)

    # Save race.csv (The 8 official numbers)
    race_file = ROOT_DIR / "week7" / "race.csv"
    summary_rows = [
        {"metric": "Pass Rate (%)", "agent": f"{agent_pass_rate:.1f}%", "fixed_workflow": f"{wf_pass_rate:.1f}%"},
        {"metric": "p50 Latency (s)", "agent": f"{agent_p50_latency:.2f}", "fixed_workflow": f"{wf_p50_latency:.2f}"},
        {"metric": "Total Tokens (10 requests)", "agent": f"{agent_total_tokens}", "fixed_workflow": f"{wf_total_tokens}"},
        {"metric": "Cost per Request ($)", "agent": f"${agent_avg_cost:.6f}", "fixed_workflow": f"${wf_avg_cost:.6f}"}
    ]

    with open(race_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "agent", "fixed_workflow"])
        writer.writeheader()
        writer.writerows(summary_rows)

    # Print clean comparison table
    print("\n" + "=" * 70)
    print("FINAL RACE RESULTS: 8 NUMBERS OVER 10 REQUESTS")
    print("=" * 70)
    print(f"{'Metric':<32} | {'ReAct Agent':<16} | {'Fixed Workflow':<16}")
    print("-" * 70)
    print(f"{'Pass Rate (%)':<32} | {agent_pass_rate:>14.1f}% | {wf_pass_rate:>14.1f}%")
    print(f"{'p50 Latency (seconds)':<32} | {agent_p50_latency:>15.2f}s | {wf_p50_latency:>15.2f}s")
    print(f"{'Total Tokens (all laps summed)':<32} | {agent_total_tokens:>16} | {wf_total_tokens:>16}")
    print(f"{'Cost per Request ($)':<32} | ${agent_avg_cost:>15.6f} | ${wf_avg_cost:>15.6f}")
    print("=" * 70)
    print(f"\nDeliverables written:\n- {race_file}\n- {details_file}")

if __name__ == "__main__":
    run_race()
