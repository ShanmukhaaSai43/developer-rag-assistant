"""
===================================================================
WEEK 9 - STEP 1 VERIFICATION & BASELINE DISCOVERY RUNNER
===================================================================
Verifies:
1. MCP Server 1 (`recipe-server`) stdio JSON-RPC handshake.
2. Dynamic tool discovery: agent reports tool count N=3 with names from tools/list.
3. Live query execution through the MCP stdio pipe.
4. Generates baseline tool discovery snapshot.
===================================================================
"""

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week9.agent import MCPRecipeReActAgent


def run_step1_verification():
    print("=" * 80)
    print("WEEK 9 - STEP 1: MCP ARCHITECTURE & BASELINE DISCOVERY VERIFICATION")
    print("=" * 80 + "\n")

    config_path = Path(__file__).resolve().parent / "mcp_servers.json"
    print(f"[1] Initializing Agent with MCP config: {config_path}")

    agent = None
    try:
        agent = MCPRecipeReActAgent(config_path=config_path)

        # 1. Report Discovered Tools
        tools_info = agent.discovered_tools_report
        total_count = tools_info["total_count"]
        tool_names = tools_info["tool_names"]
        print(f"\n[2] Dynamic Tool Discovery Result:")
        print(f"    Total tools discovered: {total_count}")
        print(f"    Tool names: {tool_names}")
        print(f"    Server breakdown: {json.dumps(tools_info['by_server'], indent=6)}")

        assert total_count == 3, f"Expected 3 tools from Server 1, got {total_count}"
        expected_tools = {"search_recipes", "scale_recipe", "substitute_ingredient"}
        assert set(tool_names) == expected_tools, f"Expected {expected_tools}, got {set(tool_names)}"
        print("    --> Assertion PASSED: Exactly 3 expected tools discovered over MCP tools/list.")

        # 2. Run Live Culinary Query
        query = "Find pasta recipe, scale it to 4 servings, and substitute heavy cream to avoid dairy."
        print(f"\n[3] Running Live Query through MCP stdio transport:")
        print(f"    Prompt: '{query}'")

        result = agent.run(query)
        print(f"\n[4] Execution Summary:")
        print(f"    Status: {result['status']}")
        print(f"    Tool sequence: {result['tool_sequence']}")
        print(f"    Trajectory steps count: {len(result['trajectory_steps'])}")
        print(f"    Tokens used: {result['metrics']['cumulative_tokens']}")
        print(f"    Duration: {result['metrics']['duration_seconds']}s")

        print(f"\n[5] Trajectory Details (Server Provenance):")
        for step in result["trajectory_steps"]:
            print(f"    Lap {step['lap']}: Tool '{step['tool']}' -> Dispatched to Server '{step['server']}'")
            print(f"        Arguments: {step['arguments']}")
            obs_preview = step['observation'][:120].replace('\n', ' ')
            print(f"        Observation: {obs_preview}...")

        # 3. Save Baseline Artifact
        baseline_record = {
            "step": "step_1_baseline",
            "server_count": 1,
            "servers": ["recipe-server"],
            "tool_count": total_count,
            "tool_names": tool_names,
            "sample_query": query,
            "tool_sequence": result["tool_sequence"],
            "trajectory_steps": result["trajectory_steps"],
            "final_answer": result["final_answer"]
        }

        out_path = Path(__file__).resolve().parent / "step1_baseline_report.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(baseline_record, f, indent=2)

        print(f"\n[6] Saved Step 1 Baseline Report to: {out_path}")
        print("\n" + "=" * 80)
        print("STEP 1 VERIFICATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    finally:
        if agent:
            agent.close()


if __name__ == "__main__":
    run_step1_verification()
