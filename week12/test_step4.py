"""
=============================================================================
WEEK 12 - STEP 4 VERIFICATION TEST: TELEMETRY & HEALTH PRIVACY
=============================================================================
Verifies:
1. One trace ID surviving across the App, Agent, and MCP hops
2. Latency and cost broken down by span
3. Health Data Privacy Boundary:
   - Stated medical health info is sanitized
   - Names redacted and severe allergy risk categorized in production.log
4. Exports representative end-to-end trace to week12/trace_sample.json
=============================================================================
"""

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week12.agent import PantryToPlateAgent
from week12.telemetry import TelemetryLogger, LOGS_DIR

def run_step4_tests():
    print("=" * 70)
    print("  STEP 4 VERIFICATION: DISTRIBUTED TELEMETRY & HEALTH PII PRIVACY")
    print("=" * 70)

    target_log_file = LOGS_DIR / "production.log"
    if target_log_file.exists():
        target_log_file.unlink()  # Fresh start for Step 4 verification

    agent = PantryToPlateAgent()
    try:
        # Prompt with sensitive health information and personal child name
        sensitive_prompt = "My daughter Maya has a severe life-threatening tree nut allergy. Can she eat the 2025 shortbread?"
        test_trace_id = "tr_maya_nut_safety_771a"

        print(f"\n[CHECK 1] Submitting Query with Health Data & Child Name:")
        print(f"  * Stated Query: '{sensitive_prompt}'")
        print(f"  * Injected Trace ID: {test_trace_id}")

        res = agent.run(sensitive_prompt, trace_id=test_trace_id)

        # Verify trace ID preservation
        print("\n[CHECK 2] Verifying Single Trace ID Across Agent & MCP Hops:")
        assert res["trace_id"] == test_trace_id, "Trace ID mismatch at agent level!"
        for span in res["spans"]:
            assert span["trace_id"] == test_trace_id, f"Span {span['span_name']} lost trace_id!"
            print(f"  * Span [{span['span_name']:<24}] -> Trace ID: {span['trace_id']} | Latency: {span['latency_ms']} ms")
        print("  * Trace ID Assertion: PASSED (One single trace ID survived all hops)")

        # Verify cost & latency breakdown
        print("\n[CHECK 3] Verifying Cost & Latency Breakdown per Span:")
        print(f"  * Total Latency: {res['total_latency_ms']} ms")
        print(f"  * Total Cost:    ${res['cost_usd']:.6f} USD")
        print(f"  * Cost Breakdown: {res['cost_breakdown']}")
        assert res["cost_usd"] > 0
        assert res["total_latency_ms"] > 0
        print("  * Cost & Latency Accounting Assertion: PASSED")

        # Verify Health Data Privacy (PII) Boundary in production.log
        print("\n[CHECK 4] Verifying Health Privacy (PII) Redaction in production.log:")
        with open(target_log_file, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
        assert len(log_lines) >= 1, "Log record was not written!"
        
        last_record = json.loads(log_lines[-1])
        sanitized_prompt = last_record["sanitized_user_prompt"]
        print(f"  * Raw Prompt:       '{sensitive_prompt}'")
        print(f"  * Sanitized Prompt: '{sanitized_prompt}'")

        # Assertions on privacy:
        assert "Maya" not in sanitized_prompt, "PII LEAK: Child's personal name was not redacted!"
        assert "[NAME_REDACTED]" in sanitized_prompt, "Expected [NAME_REDACTED] in sanitized prompt"
        assert "[MEDICAL_SEVERITY: HIGH]" in sanitized_prompt, "Expected medical risk categorization tag"
        print("  * Privacy Boundary Assertion: PASSED (Maya redacted, medical risk categorized)")

        # Export sample trace for submission checklist
        sample_trace_path = Path(__file__).resolve().parent / "trace_sample.json"
        with open(sample_trace_path, "w", encoding="utf-8") as f:
            json.dump(last_record, f, indent=2)
        print(f"\n[CHECK 5] Exported End-to-End Trace Artifact: {sample_trace_path}")

        print("\n" + "=" * 70)
        print("  ALL STEP 4 TELEMETRY & PRIVACY TESTS PASSED (100% COMPLIANT)")
        print("=" * 70)

    finally:
        agent.close()

if __name__ == "__main__":
    run_step4_tests()
