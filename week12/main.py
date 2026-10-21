"""
=============================================================================
WEEK 12 CAPSTONE: PANTRY-TO-PLATE ASSISTANT (SINGLE ENTRY POINT)
=============================================================================
One command a stranger can clone and run:
  python -m week12.main
  python -m week12.main --eval
  python -m week12.main --trajectory
  python -m week12.main --closed-loop

Integrates:
- Week 3-4 RAG & Versioned Citations
- Week 7 ReAct Hand-Built Agent Loop
- Week 9 MCP Tool Discovery over JSON-RPC 2.0
- Week 11 Distributed Telemetry & Health PII Protection
=============================================================================
"""

import sys
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week12.agent import PantryToPlateAgent
from week12.init_db import init_database, DB_PATH

def print_banner():
    print("=" * 75)
    print("  PANTRY-TO-PLATE KITCHEN ASSISTANT -- WEEK 12 CAPSTONE")
    print("  Version 1.0.0 (Production & Integrated System)")
    print("=" * 75)

def run_cli_query(query: str):
    if not DB_PATH.exists():
        print("[*] Initializing local database ledger...")
        init_database()
        
    agent = PantryToPlateAgent()
    try:
        print(f"\n[QUERY] {query}")
        print("[*] Dispatching to Head Chef Agent with runtime MCP tool discovery...")
        res = agent.run(query)
        print("\n" + "-" * 75)
        print(res["output"])
        print("-" * 75)
        print(f"\n[TELEMETRY] Trace ID: {res['trace_id']} | Spans: {len(res['spans'])} | Total Latency: {res['total_latency_ms']} ms | Cost: ${res['cost_usd']:.6f} USD")
        print(f"[TOOLS] Called: {res['tools_called']}")
    finally:
        agent.close()

def interactive_loop():
    print_banner()
    if not DB_PATH.exists():
        print("[*] Initializing local database ledger...")
        init_database()
        
    print("\nWelcome! Ask any cooking, pantry, scaling, or allergy safety question.")
    print("Type 'exit' or 'quit' to end session.\n")
    
    agent = PantryToPlateAgent()
    try:
        while True:
            try:
                user_input = input("Chef > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("\nGoodbye, Chef!")
                    break
                print("\n[*] Thinking and checking kitchen ledger over MCP...")
                res = agent.run(user_input)
                print("\n" + res["output"])
                print(f"\n[Trace ID: {res['trace_id']} | Latency: {res['total_latency_ms']}ms | Cost: ${res['cost_usd']:.6f}]\n")
            except (KeyboardInterrupt, EOFError):
                print("\nSession ended.")
                break
    finally:
        agent.close()

def main():
    parser = argparse.ArgumentParser(description="Pantry-to-Plate Assistant - Week 12 Capstone")
    parser.add_argument("--query", "-q", type=str, help="Single question to ask the assistant")
    parser.add_argument("--eval", action="store_true", help="Run the full 30-case evaluation suite")
    parser.add_argument("--trajectory", action="store_true", help="Run the trajectory eval and compute gap")
    parser.add_argument("--closed-loop", action="store_true", help="Run the closed failure-to-test loop demo")
    parser.add_argument("--ui", "--serve", action="store_true", help="Launch the Web UI & API server on http://127.0.0.1:8000")
    
    args = parser.parse_args()
    
    if args.eval:
        from week12.run_evals import run_evaluation_suite
        run_evaluation_suite(limit=30)
    elif args.trajectory:
        from week12.trajectory_eval import run_trajectory_evaluation
        run_trajectory_evaluation()
    elif args.closed_loop:
        from week12.closed_loop_test import run_closed_loop_demonstration
        run_closed_loop_demonstration()
    elif args.ui:
        from week12.api_server import run_server
        run_server(port=8000)
    elif args.query:
        run_cli_query(args.query)
    else:
        interactive_loop()

if __name__ == "__main__":
    main()
