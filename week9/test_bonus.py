"""
===================================================================
WEEK 9 - BONUS CHALLENGE VERIFICATION RUNNER
===================================================================
Validates:
1. Unified MCP Gateway exposes single front door.
2. Gateway aggregates tools and writes audit log lines.
3. Scoped token permits allergen lookup but denies nutrition facts with
   an actionable, recoverable message.
===================================================================
"""

import sys
import json
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
WEEK9_DIR = Path(__file__).resolve().parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def run_bonus_verification():
    print("=" * 80)
    print("WEEK 9 - BONUS CHALLENGE: GATEWAY & TOKEN-SCOPED ACCESS CONTROL")
    print("=" * 80 + "\n")

    audit_file = WEEK9_DIR / "audit.log"
    if audit_file.exists():
        audit_file.unlink()

    # Launch Gateway as a stdio subprocess
    p = subprocess.Popen(
        [sys.executable, "-m", "week9.gateway"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        encoding="utf-8",
        cwd=str(ROOT_DIR)
    )

    try:
        # 1. Initialize Gateway
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"clientInfo": {"name": "bonus-test-client"}}
        }
        p.stdin.write(json.dumps(init_req) + "\n")
        p.stdin.flush()
        init_resp = json.loads(p.stdout.readline())
        print(f"[1] Gateway Initialized: {init_resp['result']['serverInfo']['name']}")

        # 2. List tools through single front door
        tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        p.stdin.write(json.dumps(tools_req) + "\n")
        p.stdin.flush()
        tools_resp = json.loads(p.stdout.readline())
        tool_names = [t["name"] for t in tools_resp["result"]["tools"]]
        print(f"\n[2] Aggregated Tools from Single Front Door ({len(tool_names)} tools):")
        print(f"    {tool_names}")
        assert len(tool_names) == 5, f"Expected 5 aggregated tools, got {len(tool_names)}"

        # 3. Call Allergen Lookup (Permitted by tok_allergen_only)
        print("\n[3] Testing Permitted Tool: 'get_ingredient_details'...")
        call1 = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_ingredient_details",
                "arguments": {"ingredient_name": "coconut cream"},
                "caller": "recipe-agent-prod"
            }
        }
        p.stdin.write(json.dumps(call1) + "\n")
        p.stdin.flush()
        resp1 = json.loads(p.stdout.readline())
        print(f"    Status: isError={resp1['result']['isError']}")
        obs1 = json.loads(resp1["result"]["content"][0]["text"])
        print(f"    Observation: {obs1['canonical_name']} -> Allergens: {obs1['allergen_flags']}")
        assert not resp1["result"]["isError"], "Allergen lookup should be permitted!"

        # 4. Call Nutrition Lookup (Denied by tok_allergen_only)
        print("\n[4] Testing Denied Tool: 'get_nutrition_facts' under scoped token...")
        call2 = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_nutrition_facts",
                "arguments": {"ingredient_name": "coconut cream", "quantity_g": 100},
                "caller": "recipe-agent-prod"
            }
        }
        p.stdin.write(json.dumps(call2) + "\n")
        p.stdin.flush()
        resp2 = json.loads(p.stdout.readline())
        print(f"    Status: isError={resp2['result']['isError']}")
        obs2 = json.loads(resp2["result"]["content"][0]["text"])
        print(f"    Recoverable Denial Message:\n    >> {obs2['message']}")
        assert resp2["result"]["isError"], "Nutrition lookup should be denied!"
        assert obs2["error_code"] == "PERMISSION_DENIED"

        # 5. Inspect Unified Audit Log
        print("\n[5] Verifying Audit Log Entries in week9/audit.log:")
        assert audit_file.exists(), "audit.log was not created!"
        with open(audit_file, "r", encoding="utf-8") as f:
            audit_lines = [l.strip() for l in f if l.strip()]

        for line in audit_lines:
            print(f"    [AUDIT ENTRY] {line}")

        assert len(audit_lines) == 2, f"Expected 2 audit lines, found {len(audit_lines)}"
        assert "STATUS=ALLOWED" in audit_lines[0]
        assert "STATUS=DENIED_INSUFFICIENT_SCOPE" in audit_lines[1]

        print("\n" + "=" * 80)
        print("BONUS CHALLENGE VERIFICATION PASSED SUCCESSFULLY!")
        print("=" * 80)

    finally:
        p.kill()


if __name__ == "__main__":
    run_bonus_verification()
