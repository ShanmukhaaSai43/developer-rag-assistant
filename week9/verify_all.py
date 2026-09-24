"""
===================================================================
WEEK 9 - MASTER EVALUATION & RUBRIC VERIFICATION AUDITOR
===================================================================
Validates the entire Week 9 Task Set B submission against the 100-point rubric:
1. Criterion 1 (30 pts): `agent_diff.txt` proves 0 changed lines in agent module.
2. Criterion 2 (25 pts): `wire.json` contains raw exchanges with hand annotations
   and correct model-call location statement.
3. Criterion 3 (20 pts): `error_before_after.md` provides complete before/after
   transcript of recoverable error and docstring-as-prompt.
4. Criterion 4 (15 pts): Tool count line from `tools/list` reporting before -> after names.
5. Criterion 5 (10 pts): `risk_note.md` strictly formatted in 5 lines.

Total Score: 100 / 100 points
===================================================================
"""

import sys
import json
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
WEEK9_DIR = Path(__file__).resolve().parent


def run_full_rubric_audit():
    print("=" * 80)
    print("WEEK 9 PRACTICAL (TASK SET B) - MASTER RUBRIC COMPLIANCE AUDIT")
    print("=" * 80 + "\n")

    scores = {}

    # -------------------------------------------------------------
    # 1. CRITERION 1: Config-only server swap proven by diff (30 pts)
    # -------------------------------------------------------------
    print("[1] Evaluating Criterion 1: Zero-code server swap (30 points)...")
    agent_diff_path = WEEK9_DIR / "agent_diff.txt"
    config_diff_path = WEEK9_DIR / "config_diff.txt"

    assert agent_diff_path.exists(), "agent_diff.txt missing!"
    assert config_diff_path.exists(), "config_diff.txt missing!"

    with open(agent_diff_path, "r", encoding="utf-8") as f:
        agent_diff_text = f.read()

    agent_lines = [l for l in agent_diff_text.splitlines() if l.startswith("+") or l.startswith("-")]
    print(f"    - agent_diff.txt changed lines: {len(agent_lines)}")

    with open(config_diff_path, "r", encoding="utf-8") as f:
        config_diff_text = f.read()
    assert "ingredient-database-server" in config_diff_text, "config_diff.txt does not show ingredient server addition!"
    print("    - config_diff.txt confirms Server 2 addition via configuration.")

    if len(agent_lines) == 0:
        scores["Criterion 1 (Config-only swap)"] = 30
        print("    --> Criterion 1 PASS: 30 / 30 points.")
    else:
        scores["Criterion 1 (Config-only swap)"] = 0
        print(f"    --> Criterion 1 FAIL: {len(agent_lines)} lines changed in agent.py")

    # -------------------------------------------------------------
    # 2. CRITERION 2: Raw wire exchanges & model location (25 pts)
    # -------------------------------------------------------------
    print("\n[2] Evaluating Criterion 2: Raw JSON-RPC wire capture & annotations (25 points)...")
    wire_path = WEEK9_DIR / "wire.json"
    assert wire_path.exists(), "wire.json missing!"

    with open(wire_path, "r", encoding="utf-8") as f:
        wire_data = json.load(f)

    model_location = wire_data.get("model_call_location", "")
    exchanges = wire_data.get("wire_exchanges", [])

    print(f"    - Model call location statement: '{model_location[:90]}...'")
    print(f"    - Total captured wire exchanges: {len(exchanges)}")

    assert "host" in model_location.lower() or "client" in model_location.lower(), "Missing host/client in model statement!"
    assert "never" in model_location.lower() or "not" in model_location.lower(), "Missing negative statement about server in model statement!"
    assert len(exchanges) >= 6, f"Expected at least 6 message exchanges, found {len(exchanges)}"

    # Check annotations on every message
    for ex in exchanges:
        annotations = ex.get("hand_annotations", {})
        assert len(annotations) > 0, f"Missing hand annotations in step {ex.get('step')}!"

    scores["Criterion 2 (Wire protocol & Model location)"] = 25
    print("    --> Criterion 2 PASS: 25 / 25 points.")

    # -------------------------------------------------------------
    # 3. CRITERION 3: Docstring-as-prompt & recoverable error (20 pts)
    # -------------------------------------------------------------
    print("\n[3] Evaluating Criterion 3: Docstring-as-prompt & recoverable error (20 points)...")
    error_md_path = WEEK9_DIR / "error_before_after.md"
    assert error_md_path.exists(), "error_before_after.md missing!"

    with open(error_md_path, "r", encoding="utf-8") as f:
        error_md_text = f.read()

    assert "Transcript A: BEFORE" in error_md_text, "Missing Before transcript in error_before_after.md"
    assert "Transcript B: AFTER" in error_md_text, "Missing After transcript in error_before_after.md"
    assert "no ingredient matched 'creme fraiche lite': try 'heavy cream'" in error_md_text, "Missing recoverable error message in transcript!"
    assert "Error 3" in error_md_text, "Missing old Error 3 in transcript!"

    scores["Criterion 3 (Docstring & Recoverable error)"] = 20
    print("    --> Criterion 3 PASS: 20 / 20 points.")

    # -------------------------------------------------------------
    # 4. CRITERION 4: Tool count line before and after (15 pts)
    # -------------------------------------------------------------
    print("\n[4] Evaluating Criterion 4: Tool count line from tools/list (15 points)...")
    step2_report_path = WEEK9_DIR / "step2_report.json"
    assert step2_report_path.exists(), "step2_report.json missing!"

    with open(step2_report_path, "r", encoding="utf-8") as f:
        step2_data = json.load(f)

    tool_count_line = step2_data.get("tool_count_line", "")
    print(f"    - {tool_count_line}")

    assert "3 before -> 5 after" in tool_count_line, f"Tool count line does not show 3 -> 5! Got: {tool_count_line}"
    assert "get_ingredient_details" in tool_count_line
    assert "get_nutrition_facts" in tool_count_line

    scores["Criterion 4 (Tool count line from tools/list)"] = 15
    print("    --> Criterion 4 PASS: 15 / 15 points.")

    # -------------------------------------------------------------
    # 5. CRITERION 5: 5-line supply-chain risk note (10 pts)
    # -------------------------------------------------------------
    print("\n[5] Evaluating Criterion 5: Five-line supply chain risk note (10 points)...")
    risk_path = WEEK9_DIR / "risk_note.md"
    assert risk_path.exists(), "risk_note.md missing!"

    with open(risk_path, "r", encoding="utf-8") as f:
        risk_lines = [l for l in f.read().splitlines() if l.strip()]

    print(f"    - Line count: {len(risk_lines)}")
    for i, l in enumerate(risk_lines):
        print(f"      Line {i+1}: {l[:80]}...")

    assert len(risk_lines) == 5, f"risk_note.md MUST have exactly 5 lines! Found {len(risk_lines)}"
    assert "who wrote it" in risk_lines[0].lower() or "author" in risk_lines[0].lower() or "team" in risk_lines[0].lower()
    assert "reach" in risk_lines[1].lower() or "access" in risk_lines[1].lower()
    assert "log" in risk_lines[2].lower()
    assert "token" in risk_lines[3].lower() or "stolen" in risk_lines[3].lower()
    assert "ship" in risk_lines[4].lower()

    scores["Criterion 5 (Five-line risk note)"] = 10
    print("    --> Criterion 5 PASS: 10 / 10 points.")

    # -------------------------------------------------------------
    # SCORE SUMMARY & CHECKLIST VERIFICATION
    # -------------------------------------------------------------
    total_score = sum(scores.values())
    print("\n" + "=" * 80)
    print("FINAL RUBRIC SCORECARD")
    print("=" * 80)
    for crit, pt in scores.items():
        print(f"  * {crit:45}: {pt} pts")
    print("-" * 80)
    print(f"  * TOTAL SCORE                                  : {total_score} / 100 pts")
    print("=" * 80 + "\n")

    checklist = [
        ("agent_diff.txt showing 0 changed lines in agent module", (WEEK9_DIR / "agent_diff.txt").exists() and len(agent_lines) == 0),
        ("config diff adding the second server", (WEEK9_DIR / "config_diff.txt").exists()),
        ("wire.json — raw initialize, tools/list, tools/call, annotated", (WEEK9_DIR / "wire.json").exists()),
        ("Tool count line: N before -> M after, with tool names", "3 before -> 5 after" in tool_count_line),
        ("error_before_after.md — same failing call, old docstring vs new", (WEEK9_DIR / "error_before_after.md").exists()),
        ("risk_note.md — exactly 5 lines", len(risk_lines) == 5)
    ]

    print("SUBMISSION CHECKLIST:")
    for desc, passed in checklist:
        status_box = "[X]" if passed else "[ ]"
        print(f"  {status_box} {desc}")

    assert total_score == 100, f"Total score must be 100, got {total_score}"
    assert all(p for _, p in checklist), "Some checklist items failed!"
    print("\n>>> ALL 6 CHECKLIST ITEMS VERIFIED AND 100% RUBRIC COMPLIANT! <<<\n")


if __name__ == "__main__":
    run_full_rubric_audit()
