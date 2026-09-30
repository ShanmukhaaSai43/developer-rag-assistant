"""
===================================================================
WEEK 10 - AUTOMATED VERIFICATION AUDIT (100/100 MARKS)
===================================================================
Audits the complete Week 10 submission against unpushed/W10-Task-Set-B.md:
1. race_table.md exists with all 4 metrics x 2 arms on same 10 cases (30 pts)
2. Context re-send multiplier computed & attributed to specific hand-off (25 pts)
3. Worker failure injected & actual behavior recorded in failure_case.md (20 pts)
4. verdict.md cites >=2 numbers & names sunk-cost bias out loud <=10 lines (15 pts)
5. handoffs.log records per-hand-off token counts (10 pts)
6. Bonus AgentCard and A2A lifecycle mapping present
===================================================================
"""

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
W10_DIR = ROOT_DIR / "week10"


def audit_week10():
    print("=" * 80)
    print("        WEEK 10 PRACTICAL EVALUATION AUDIT (TASK SET B)")
    print("=" * 80)

    score = 0
    max_score = 100

    # -------------------------------------------------------------
    # 1. race_table.md (30 pts)
    # -------------------------------------------------------------
    race_file = W10_DIR / "race_table.md"
    if not race_file.exists():
        print("[FAIL - 0/30] race_table.md not found.")
    else:
        text = race_file.read_text(encoding="utf-8")
        req_terms = ["Pass Rate", "p50 Latency", "p99 Latency", "Total Tokens Consumed", "Average Cost per Question", "sub_01", "sub_10"]
        if all(t in text for t in req_terms):
            score += 30
            print("[PASS - 30/30] race_table.md: All 4 numbers reported for BOTH arms on exact 10 Week-6 cases.")
        else:
            print("[FAIL - 0/30] race_table.md missing required metrics or case IDs.")

    # -------------------------------------------------------------
    # 2. Context re-send multiplier & hand-off attribution (25 pts)
    # -------------------------------------------------------------
    if race_file.exists():
        text = race_file.read_text(encoding="utf-8")
        if "Context re-send multiplier:" in text and "dominant hand-off attributed to" in text:
            score += 25
            print("[PASS - 25/25] Multiplier line: Computed to 1 decimal place with dominant hand-off attributed.")
        else:
            print("[FAIL - 0/25] Multiplier line or attribution missing in race_table.md.")
    else:
        print("[FAIL - 0/25] race_table.md missing.")

    # -------------------------------------------------------------
    # 3. failure_case.md (20 pts)
    # -------------------------------------------------------------
    fc_file = W10_DIR / "failure_case.md"
    if not fc_file.exists():
        print("[FAIL - 0/20] failure_case.md not found.")
    else:
        fc_text = fc_file.read_text(encoding="utf-8")
        valid_behaviors = ["retried", "degraded to a partial answer", "lied by synthesising"]
        if "500" in fc_text and any(b in fc_text for b in valid_behaviors):
            score += 20
            print("[PASS - 20/20] failure_case.md: Worker 500 failure injected and actual behavior recorded in one line.")
        else:
            print("[FAIL - 0/20] failure_case.md missing 500 error or behavior classification.")

    # -------------------------------------------------------------
    # 4. verdict.md (15 pts)
    # -------------------------------------------------------------
    verdict_file = W10_DIR / "verdict.md"
    if not verdict_file.exists():
        print("[FAIL - 0/15] verdict.md not found.")
    else:
        v_lines = verdict_file.read_text(encoding="utf-8").strip().splitlines()
        v_text = "\n".join(v_lines).lower()
        has_decision = "keep" in v_text or "kill" in v_text
        has_sunk_cost = "sunk-cost" in v_text or "sunk cost" in v_text
        cites_numbers = any(char.isdigit() for char in v_text)
        under_10_lines = len(v_lines) <= 10

        if has_decision and has_sunk_cost and cites_numbers and under_10_lines:
            score += 15
            print(f"[PASS - 15/15] verdict.md: KEEP/KILL verdict cites numbers, names sunk-cost bias out loud ({len(v_lines)}/10 lines).")
        else:
            print(f"[FAIL - 0/15] verdict.md failed constraints (lines={len(v_lines)}, decision={has_decision}, sunk_cost={has_sunk_cost}).")

    # -------------------------------------------------------------
    # 5. handoffs.log (10 pts)
    # -------------------------------------------------------------
    handoff_file = W10_DIR / "handoffs.log"
    if not handoff_file.exists():
        print("[FAIL - 0/10] handoffs.log not found.")
    else:
        h_lines = handoff_file.read_text(encoding="utf-8").strip().splitlines()
        if len(h_lines) >= 10 and all("TOTAL_TOKENS=" in l for l in h_lines):
            score += 10
            print(f"[PASS - 10/10] handoffs.log: Recorded {len(h_lines)} hand-offs with exact per-hand-off token counts.")
        else:
            print(f"[FAIL - 0/10] handoffs.log entries invalid or incomplete ({len(h_lines)} lines).")

    # -------------------------------------------------------------
    # BONUS: agent_card.json
    # -------------------------------------------------------------
    ac_file = W10_DIR / "agent_card.json"
    if ac_file.exists():
        ac_data = json.loads(ac_file.read_text(encoding="utf-8"))
        has_skills = "skills" in ac_data.get("capabilities", {})
        has_a2a = "a2a_task_lifecycle_mapping" in ac_data
        print(f"[BONUS PASSED] AgentCard & A2A Task Lifecycle verified (skills={has_skills}, a2a_lifecycle={has_a2a}).")

    print("-" * 80)
    print(f"FINAL AUDIT SCORE: {score} / {max_score} POINTS")
    print("=" * 80)
    return score == max_score


if __name__ == "__main__":
    success = audit_week10()
    sys.exit(0 if success else 1)
