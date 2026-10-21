# Fresh-Eyes Peer Review Audit Note

**Date:** Thursday, October 16, 2026  
**External Reviewer:** Priya S. (Squad 4 — Claims & Policy Engine)  
**Artifact Inspected:** `week12/mcp_server.py` and `week12/main.py`  
**Protocol Tested:** Standard Model Context Protocol (MCP) JSON-RPC 2.0 over stdio transport  

---

## 1. What the External Reviewer Ran
Priya connected her squad's external Python agent runner to our MCP Server (`week12.mcp_server`) to test cross-squad interoperability:
```json
{
  "mcpServers": {
    "squad-b-recipe-server": {
      "command": ".venv/Scripts/python.exe",
      "args": ["-m", "week12.mcp_server"]
    }
  }
}
```
She ran 15 live queries against our tools (`search_recipes`, `check_recipe_allergens`, `scale_recipe_ingredients`, `get_food_safety_rule`).

---

## 2. Where the Reviewer Stumbled
1. **Parameter Type Coercion:**  
   Priya's client serialized `target_servings` as a string (`"8"`) rather than a strict integer (`8`), which initially raised a Python `TypeError` inside the scaling math.
2. **Missing Recipe Version in Citation:**  
   Her external agent extracted the `title` and `id` but discarded the `version` field (`reformulated-2025`), leading her client to state that Scottish Shortbread was nut-free because it defaulted to the original recipe card.
3. **Pipe Buffer Deadlock:**  
   When her test suite ran 40 tool calls in a tight loop, her test harness hung due to unread `stderr` pipe buffer exhaustion on Windows.

---

## 3. What We Changed in Response to Feedback
1. **Added Defensive Type Coercion:**  
   Updated `week12/tools.py` (`scale_recipe_ingredients`) to cast `int(target_servings)` with bounds checking, preventing string serialization crashes from external callers.
2. **Promoted `version` to Top-Level Response Object:**  
   Restructured all MCP tool payloads so that `version` (`original` vs `reformulated-2025`) is an explicit top-level key and cannot be missed by third-party clients.
3. **OS Pipe Deadlock Fix (SEAM-08):**  
   Configured `stderr=subprocess.DEVNULL` in our client harness and documented stdio pipe draining in `README.md` for external developers.
