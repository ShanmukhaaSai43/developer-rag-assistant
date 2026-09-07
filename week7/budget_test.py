"""
===================================================================
WEEK 7 - STEP 5: BUDGET TERMINATION DEMONSTRATION
===================================================================
Proves that the agent enforces its execution budgets and terminates
cleanly when a limit is reached.
Saves the proof log to `week7/budget_termination.log`.
===================================================================
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from week7.agent import RecipeReActAgent

def run_budget_test():
    log_file = ROOT_DIR / "week7" / "budget_termination.log"
    print("=== RUNNING STEP 5: BUDGET TERMINATION TEST ===")
    
    # We set a tight limit of max_iterations=2 on a complex request
    tight_agent = RecipeReActAgent(
        max_iterations=2,        # Strict limit of 2 laps
        max_tokens=20_000,
        max_cost=0.05,
        wall_clock_timeout=25.0
    )

    query = "Find Classic Peanut Butter Cookies, scale to 4 servings. The diner has a severe peanut allergy AND a tree nut allergy, so replace peanut butter with something safe from both."
    
    print(f"Setting strict budget: max_iterations = {tight_agent.max_iterations}")
    print(f"User Request: '{query}'\n")

    result = tight_agent.run(query)

    print("\n=== TERMINATION OUTCOME ===")
    print(f"Status:          {result['status']}")
    print(f"Budget Triggered: {result['budget_fired']}")
    print(f"Laps Completed:  {result['laps_completed']}")
    print(f"Clean Exit:      True (Halted safely without infinite looping)")

    # Save human-readable log file
    log_lines = [
        "===================================================================",
        "WEEK 7 - BUDGET-TRIGGERED TERMINATION LOG",
        "===================================================================",
        f"Model: {tight_agent.model_name}",
        f"Configured Budgets:",
        f"  - max_iterations: {tight_agent.max_iterations}",
        f"  - max_tokens: {tight_agent.max_tokens}",
        f"  - max_cost: ${tight_agent.max_cost}",
        f"  - wall_clock_timeout: {tight_agent.wall_clock_timeout}s",
        "-------------------------------------------------------------------",
        f"User Query: {query}",
        "-------------------------------------------------------------------",
        "TERMINATION RESULT:",
        f"  Status: {result['status']}",
        f"  Budget Fired: {result['budget_fired']}",
        f"  Laps Executed: {result['laps_completed']}",
        f"  Clean Exit: True (No infinite loop, terminated safely)",
        "==================================================================="
    ]

    log_content = "\n".join(log_lines)
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(log_content)

    print(f"\nProof log saved to: {log_file}")
    assert result["status"] == "budget_exceeded"
    assert result["budget_fired"] == "max_iterations"
    print("Test passed! Budget enforcement verified.")

if __name__ == "__main__":
    run_budget_test()
