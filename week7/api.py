"""
===================================================================
WEEK 7: FASTAPI BACKEND API
===================================================================
Exposes REST endpoints for the Week 7 Recipe Adaptation systems:
1. POST /api/run-agent      -> Runs RecipeReActAgent (autonomous loop)
2. POST /api/run-workflow   -> Runs Fixed Recipe Workflow (3 hardcoded steps)
3. POST /api/race           -> Races both systems concurrently on the same request
4. GET  /api/presets        -> Benchmark test cases from dataset.py
===================================================================
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure repo root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week7.agent import RecipeReActAgent
from week7.workflow import RecipeFixedWorkflow
from week7.dataset import BENCHMARK_REQUESTS, evaluate_recipe

app = FastAPI(
    title="Week 7: Recipe Agent vs Fixed Workflow API",
    description="Interactive backend comparing autonomous ReAct agent loops against deterministic workflows.",
    version="1.0.0"
)

# Enable CORS for frontend Vite dev server (localhost:5173, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecipeRequest(BaseModel):
    prompt: str
    preset_id: Optional[str] = None
    target_servings: Optional[int] = 4
    avoid_allergens: Optional[List[str]] = None
    request_type: Optional[str] = "standard"
    intermediate_allergen_sub: Optional[str] = ""
    terminal_safe_sub: Optional[str] = ""


def _build_request_case(req: RecipeRequest) -> Dict[str, Any]:
    """Helper to match request case with dataset schema for evaluation."""
    if req.preset_id:
        for p in BENCHMARK_REQUESTS:
            if p["id"] == req.preset_id:
                return p
    return {
        "id": "custom",
        "type": req.request_type or "standard",
        "query": req.prompt,
        "target_servings": req.target_servings or 4,
        "avoid_allergens": req.avoid_allergens or [],
        "intermediate_allergen_sub": req.intermediate_allergen_sub or "",
        "terminal_safe_sub": req.terminal_safe_sub or ""
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": time.time()}


@app.get("/api/presets")
def get_presets():
    """Returns the 10 benchmark test cases used in the evaluation rubric."""
    return {"presets": BENCHMARK_REQUESTS}


@app.post("/api/run-agent")
def api_run_agent(req: RecipeRequest):
    """Executes the autonomous ReAct agent with 4 enforced budgets."""
    try:
        agent = RecipeReActAgent()
        result = agent.run(req.prompt)
        
        request_case = _build_request_case(req)
        grade = evaluate_recipe(request_case, result.get("final_recipe"))
        
        return {
            "system": "agent",
            "status": result.get("status"),
            "passed": grade["passed"],
            "grade_errors": grade.get("errors", []),
            "latency_seconds": result.get("latency_seconds", 0.0),
            "total_tokens": result.get("total_tokens", 0),
            "total_cost_usd": result.get("total_cost_usd", 0.0),
            "laps_completed": result.get("laps_completed", 0),
            "budget_fired": result.get("budget_fired"),
            "final_recipe": result.get("final_recipe"),
            "raw_output": result.get("raw_output", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/run-workflow")
def api_run_workflow(req: RecipeRequest):
    """Executes the fixed deterministic 3-step workflow (zero loops)."""
    try:
        workflow = RecipeFixedWorkflow()
        result = workflow.run(req.prompt)
        
        request_case = _build_request_case(req)
        grade = evaluate_recipe(request_case, result.get("final_recipe"))
        
        return {
            "system": "workflow",
            "status": result.get("status"),
            "passed": grade["passed"],
            "grade_errors": grade.get("errors", []),
            "latency_seconds": result.get("latency_seconds", 0.0),
            "total_tokens": result.get("total_tokens", 0),
            "total_cost_usd": result.get("total_cost_usd", 0.0),
            "steps_completed": result.get("steps_completed", 3),
            "final_recipe": result.get("final_recipe")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/race")
def api_race(req: RecipeRequest):
    """Executes both systems and returns comparative side-by-side metrics."""
    agent_resp = api_run_agent(req)
    workflow_resp = api_run_workflow(req)

    comparison = {
        "pass_winner": "tie" if agent_resp["passed"] == workflow_resp["passed"] else ("agent" if agent_resp["passed"] else "workflow"),
        "latency_winner": "workflow" if workflow_resp["latency_seconds"] < agent_resp["latency_seconds"] else "agent",
        "tokens_winner": "workflow" if workflow_resp["total_tokens"] < agent_resp["total_tokens"] else "agent",
        "cost_winner": "workflow" if workflow_resp["total_cost_usd"] < agent_resp["total_cost_usd"] else "agent"
    }

    return {
        "prompt": req.prompt,
        "agent": agent_resp,
        "workflow": workflow_resp,
        "comparison": comparison
    }


# Mount compiled React UI for single-command serving
UI_DIST_DIR = Path(__file__).resolve().parent / "ui" / "dist"
if UI_DIST_DIR.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(UI_DIST_DIR), html=True), name="static_ui")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("week7.api:app", host="127.0.0.1", port=8000, reload=True)
