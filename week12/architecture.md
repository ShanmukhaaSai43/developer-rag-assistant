# One-Page Architecture Sketch — Pantry-to-Plate Assistant

```
                                  [ Strangers / External Clients / Web UI ]
                                                     │
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │   Single Entry Point CLI     │
                                      │     (week12/main.py)         │
                                      └──────────────┬───────────────┘
                                                     │
                                            [ Injects trace_id ]
                                                     │
                                                     ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       AUTONOMOUS HEAD CHEF AGENT                                           │
│                                           (week12/agent.py)                                                │
│                                                                                                            │
│   ┌──────────────────────────┐                                                                             │
│   │   System Instruction:    │ ◄── [Prompt Version: v1.2.0]                                                │
│   │   - Versioned Citations  │                                                                             │
│   │   - Cook Time Invariance │                                                                             │
│   │   - 74°C Chicken Safety  │                                                                             │
│   │   - Honest Refusals      │                                                                             │
│   └─────────────┬────────────┘                                                                             │
│                 │                                                                                          │
│                 ▼                                                                                          │
│   ┌──────────────────────────┐  [Generates Tool Call]   ┌──────────────────────────────────────────────┐  │
│   │  LLM REASONING LOOP      ├─────────────────────────►│  MCP Client Runtime Tool Dispatcher         │  │
│   │  (gemini-3.5-flash-lite) │                          │  (week12/mcp_client.py)                      │  │
│   └─────────────▲────────────┘                          └──────────────────────┬───────────────────────┘  │
│                 │                                                              │                          │
│                 │ [Tool Observation]                                          │ [JSON-RPC stdio]          │
│                 │                                                              ▼                          │
│                 │                                       ┌──────────────────────────────────────────────┐  │
│                 │                                       │   PANTRY-TO-PLATE MCP SERVER                 │  │
│                 │                                       │   (week12/mcp_server.py)                     │  │
│                 │                                       ├──────────────────────────────────────────────┤  │
│                 │                                       │ • search_recipes                             │  │
│                 │                                       │ • check_recipe_allergens (Exact Match)       │  │
│                 │                                       │ • scale_recipe_ingredients (Time Invariant)  │  │
│                 │                                       │ • get_food_safety_rule (74°C Poultry)        │  │
│                 │                                       │ • substitute_ingredient (Inherent Allergens) │  │
│                 │                                       └──────────────────────┬───────────────────────┘  │
│                 │                                                              │                          │
│                 │                                                              ▼                          │
│                 │                                       ┌──────────────────────────────────────────────┐  │
│                 │                                       │   LOCAL KITCHEN LEDGER                       │  │
│                 │                                       │   (week12/data/recipes.db)                   │  │
│                 │                                       │ • 600 Recipes (80 Reformulated Pairs)        │  │
│                 │                                       │ • Structured Allergens (contains/may)        │  │
│                 │                                       │ • Test Kitchen Substitutions                 │  │
│                 │                                       └──────────────────────────────────────────────┘  │
│                 │                                                                                         │
│                 ▼                                                                                         │
│   ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│   │                                DISTRIBUTED TELEMETRY & HEALTH PII                                  │  │
│   │                                      (week12/telemetry.py)                                         │  │
│   │  • One single trace_id surviving all hops (App -> Agent -> MCP -> DB)                              │  │
│   │  • Granular Latency (ms) & Cost (USD) per span                                                     │  │
│   │  • Health PII Sanitizer: Redacts family names & categorizes anaphylaxis risk in production.log     │  │
│   └────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Where the Money Goes (Cost Model per Query)

$$\text{Total Cost per Query} = \mathbf{\$0.000341\text{ USD}}$$

1. **LLM Input Context (~3,653 tokens):** $\$0.000274$ ($0.075 / 1\text{M tokens}$).
2. **LLM Output Generation (~157 tokens):** $\$0.000047$ ($0.300 / 1\text{M tokens}$).
3. **MCP Tool Wire Spans (2 tool calls):** $\$0.000020$ (Local SQLite query execution).
4. **Daily Burn at 50,000 queries/day:** $\$17.05\text{ USD/day}$ (\$511.50/month).
