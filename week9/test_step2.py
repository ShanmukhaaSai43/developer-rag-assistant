"""
===================================================================
WEEK 9 - STEP 2 VERIFICATION & ZERO-CODE EXTENSION RUNNER
===================================================================
Verifies:
1. Agent dynamically discovers Server 2 without any code changes.
2. Tool count moves from N=3 to M=5, with names taken directly from `tools/list`.
3. Runs live query that provably invokes tools from Server 2 in the execution trace.
4. Generates `agent_diff.txt` (0 changed lines) and `config_diff.txt`.
===================================================================
"""

import sys
import json
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week9.agent import MCPRecipeReActAgent


def run_step2_verification():
    print("=" * 80)
    print("WEEK 9 - STEP 2: ZERO-CODE SERVER SWAP & DYNAMIC EXPANSION VERIFICATION")
    print("=" * 80 + "\n")

    config_path = Path(__file__).resolve().parent / "mcp_servers.json"
    baseline_path = Path(__file__).resolve().parent / "step1_baseline_report.json"

    # 1. Load Step 1 baseline tool count
    if not baseline_path.exists():
        raise FileNotFoundError(f"Step 1 baseline report not found at {baseline_path}")

    with open(baseline_path, "r", encoding="utf-8") as f:
        step1_baseline = json.load(f)

    tools_before_count = step1_baseline["tool_count"]
    tools_before_names = step1_baseline["tool_names"]

    print(f"[1] Baseline (Server 1 only):")
    print(f"    Tools before: {tools_before_count} -> {tools_before_names}")

    # 2. Connect Agent with Server 1 + Server 2 Config
    print(f"\n[2] Connecting Agent to configured servers (Server 1 + Server 2)...")
    agent = None
    try:
        agent = MCPRecipeReActAgent(config_path=config_path)
        discovered = agent.discovered_tools_report
        tools_after_count = discovered["total_count"]
        tools_after_names = discovered["tool_names"]
        by_server = discovered["by_server"]

        print(f"\n[3] Tools Discovery After Adding Server 2:")
        print(f"    Tools after: {tools_after_count} -> {tools_after_names}")
        print(f"    Server breakdown: {json.dumps(by_server, indent=6)}")

        # Tool count assertion
        tool_count_line = f"Tool count line: {tools_before_count} before -> {tools_after_count} after, with tool names: {tools_after_names}"
        print(f"\n    [RUBRIC CRITERION 4] {tool_count_line}")

        assert tools_after_count == 5, f"Expected 5 tools, got {tools_after_count}"
        assert "get_ingredient_details" in tools_after_names
        assert "get_nutrition_facts" in tools_after_names
        print("    --> Assertion PASSED: 5 tools discovered dynamically via tools/list.")

        # 3. Run Query Provably Calling Server 2
        query = (
            "Check the allergen flags for coconut cream and get its nutrition facts per 100g. "
            "Also check how many calories are in 100g of heavy cream."
        )
        print(f"\n[4] Running query requiring Server 2 tools:")
        print(f"    Prompt: '{query}'")

        result = agent.run(query)

        print(f"\n[5] Execution Result:")
        print(f"    Status: {result['status']}")
        print(f"    Tool sequence: {result['tool_sequence']}")
        print(f"    Duration: {result['metrics']['duration_seconds']}s")
        print(f"    Total laps: {result['metrics']['total_laps']}")

        print(f"\n[6] Server Provenance in Trace:")
        server2_calls = []
        for step in result["trajectory_steps"]:
            print(f"    Lap {step['lap']}: Tool '{step['tool']}' -> Dispatched to Server '{step['server']}'")
            print(f"        Arguments: {step['arguments']}")
            obs_preview = step['observation'][:120].replace('\n', ' ')
            print(f"        Observation: {obs_preview}...")
            if step["server"] == "ingredient-database-server":
                server2_calls.append(step)

        assert len(server2_calls) > 0, "No tools were called from ingredient-database-server!"
        print(f"\n    --> PROOF PASSED: {len(server2_calls)} tool calls provably executed against 'ingredient-database-server'.")

        # 4. Generate Git Diffs
        print("\n[7] Generating Rubric Deliverables: agent_diff.txt and config_diff.txt...")
        
        # Git diff for agent module
        agent_diff_proc = subprocess.run(
            ["git", "diff", "HEAD", "week9/agent.py"],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR)
        )
        agent_diff_content = agent_diff_proc.stdout
        agent_diff_path = Path(__file__).resolve().parent / "agent_diff.txt"
        with open(agent_diff_path, "w", encoding="utf-8") as f:
            f.write(agent_diff_content)

        agent_changed_lines = len([l for l in agent_diff_content.splitlines() if l.startswith("+") or l.startswith("-")])
        print(f"    agent_diff.txt saved to: {agent_diff_path}")
        print(f"    Changed lines in agent.py: {agent_changed_lines}")
        assert agent_changed_lines == 0, f"Expected 0 changed lines in agent.py, found {agent_changed_lines}"
        print("    --> ZERO LINES CHANGED PROVEN: Agent module untouched!")

        # Git diff for config
        config_diff_proc = subprocess.run(
            ["git", "diff", "HEAD", "week9/mcp_servers.json"],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR)
        )
        config_diff_content = config_diff_proc.stdout
        config_diff_path = Path(__file__).resolve().parent / "config_diff.txt"
        with open(config_diff_path, "w", encoding="utf-8") as f:
            f.write(config_diff_content)
        print(f"    config_diff.txt saved to: {config_diff_path}")

        # 5. Save Step 2 Report
        report_data = {
            "step": "step_2_server2_addition",
            "tool_count_line": tool_count_line,
            "tools_before": {
                "count": tools_before_count,
                "names": tools_before_names
            },
            "tools_after": {
                "count": tools_after_count,
                "names": tools_after_names,
                "by_server": by_server
            },
            "agent_diff_lines_changed": agent_changed_lines,
            "test_query": query,
            "tool_sequence": result["tool_sequence"],
            "server2_tool_calls": [
                {"tool": c["tool"], "server": c["server"], "arguments": c["arguments"]}
                for c in server2_calls
            ],
            "metrics": result["metrics"],
            "final_answer": result["final_answer"]
        }

        report_path = Path(__file__).resolve().parent / "step2_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        print(f"    Step 2 Report saved to: {report_path}")

        print("\n" + "=" * 80)
        print("STEP 2 VERIFICATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    finally:
        if agent:
            agent.close()


if __name__ == "__main__":
    run_step2_verification()
