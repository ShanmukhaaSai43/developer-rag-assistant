# 🍽️ Pantry-to-Plate Assistant — React UI

A modern, responsive, glassmorphic dark-mode web dashboard for the Week 12 Capstone culinary agent.

## ✨ Features
1. **💬 Head Chef Chat & Agent Stream:**
   - Real-time conversation with the ReAct agent powered by `gemini-3.5-flash-lite`.
   - Hostile question chips (2025 shortbread nut check, portion scaling, 74°C poultry rule).
   - Real-time telemetry inspector on every message: `trace_id`, latency in ms, cost in USD, and exact MCP tools invoked.
2. **📖 600-Recipe Catalog & 2025 Audit:**
   - Visual catalog cards displaying prep time, base servings, and exact allergen badges.
   - Side-by-side audit of **original** (dairy butter) vs. **reformulated-2025** (macadamia/walnut oil).
   - Anaphylaxis risk alerts.
3. **⚖️ Portion Scaler with Invariant Bake Time:**
   - Interactive slider from 1 to 64 servings.
   - Live mathematical scaling of ingredient quantities.
   - Prominently enforces the **25-minute bake time invariance** lock.
4. **🛡️ Closed Failure Loop Demonstration:**
   - Visual 3-phase interactive runner: **Phase 1 RED** (naive almond butter failure) ➔ **Phase 2 FIX** (downstream allergen interceptor) ➔ **Phase 3 GREEN** (permanent safe oat/coconut pass).
5. **📊 Rubric Metrics & Economics:**
   - Highlights *A Number That Moved* (-83.3% allergen drop).
   - 96.7% LLM Judge Agreement.
   - +25.0% Outcome-vs-Trajectory Gap.
   - $0.000341/query unit economics ($17.05/day @ 50,000 queries).

---

## 🚀 How to Run

### Option 1: Direct Single Command (Production Build on Port 8000)
```bash
# From repository root:
.venv/Scripts/python.exe -m week12.main --ui
# Open http://127.0.0.1:8000
```

### Option 2: Vite Dev Server with Hot-Reloading (Port 5173)
```bash
# Terminal 1: Start API server
.venv/Scripts/python.exe -m week12.main --ui

# Terminal 2: Start Vite Dev Server
cd pantry-ui
npm run dev
# Open http://localhost:5173
```
