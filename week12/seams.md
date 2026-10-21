# Tuesday's Unedited Seam List — Pantry-to-Plate Assistant

This document records the exact integration friction points ("seams") identified when joining the RAG pipeline, the hand-built agent loop, and the MCP server.

| Seam ID | Component Seam | Issue Description | Severity | Status |
|:---:|:---|:---|:---:|:---:|
| **SEAM-01** | **LLM Gateway ↔ Gemini Endpoint** | `gemini-2.5-flash-lite` returned upstream 404 deprecation. | Critical | **FIXED** — Updated to active production model `gemini-3.5-flash-lite`. |
| **SEAM-02** | **MCP Protocol ↔ Stdio Transport** | Standard `print()` diagnostic messages to stdout corrupted the JSON-RPC message framing parser. | High | **FIXED** — Routed all server logging strictly to `sys.stderr`; stdout is reserved exclusively for JSON-RPC 2.0 frames. |
| **SEAM-03** | **Retriever ↔ Allergen Safety** | Treating allergen declarations as prose in semantic vector search risked missing "may contain" flags or misjudging nut oils. | Critical (Life-Safety) | **FIXED** — Implemented exact-match structured field assertions in `check_recipe_allergens` directly against the database ledger. |
| **SEAM-04** | **Agent Reasoning ↔ Scaling Tool** | When scaling batch size 4×, LLM tended to scale baking time from 25 minutes to 100 minutes, burning the dish. | High (Culinary) | **FIXED** — Tool returns explicit `cook_time_rule` invariant locking bake time constant; agent prompt explicitly forbids multiplying cooking duration. |
| **SEAM-05** | **Agent Output ↔ Version Citations** | Standard citations only named the dish title or generic ID without declaring whether it used the original or reformulated-2025 recipe. | Critical (Legal / Allergy) | **FIXED** — Enforced mandatory clickable citation format `[recipe_id (version)]` across system instructions and evaluation assertions. |
| **SEAM-06** | **Substitution Chain ↔ Downstream Allergens** | Substituting cow's milk with almond milk resolved a dairy request but introduced an unannounced tree nut allergen downstream. | High | **ACCEPTED** — Guarded by `substitute_ingredient` inherent allergen metadata and bonus eval assertion. |
| **SEAM-07** | **Windows Console Encoding ↔ Telemetry Output** | Unicode emoji characters in test logs triggered Windows `cp1252` encoding exceptions on standard terminal output. | Low | **FIXED** — Replaced unicode glyphs with resilient ASCII status markers (`[SAFE]`, `[DANGER]`, `*`). |
| **SEAM-08** | **MCP Subprocess ↔ OS Pipe Buffer Deadlock** | When `mcp_server` logged diagnostics to `stderr=PIPE`, the Windows 4KB OS buffer filled up after ~25 calls, causing child write-block and client deadlock. | High | **FIXED** — Configured `stderr=subprocess.DEVNULL` on child process, eliminating OS pipe capacity limits during continuous eval loops. |
