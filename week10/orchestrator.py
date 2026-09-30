"""
===================================================================
WEEK 10 - ARM 2: MULTI-AGENT ORCHESTRATOR (KITCHEN SQUAD MANAGER)
===================================================================
Orchestrator that:
1. Decomposes cooking question into specialized sub-tasks.
2. Delegates to Specialist 1: `substitution_worker`.
3. Delegates to Specialist 2: `allergen_worker`.
4. Synthesizes final verified culinary answer from worker findings.
5. Accurately measures per-hand-off tokens and logs to `handoffs.log`.
6. Handles graceful degradation if a specialist returns 500.
===================================================================
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

from google.genai import types
from week10.gemini_client import get_gemini_client, safe_generate_content
from week10.workers.substitution_worker import run_substitution_worker
from week10.workers.allergen_worker import run_allergen_worker

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[ORCHESTRATOR] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("orchestrator")

HANDOFFS_LOG_FILE = ROOT_DIR / "week10" / "handoffs.log"

SYNTHESIS_SYSTEM_INSTRUCTION = """You are the Kitchen Squad Lead and Master Culinary Synthesizer.
You receive specialist reports from:
1. Substitution Worker (structural integrity, chemical viability, texture).
2. Allergen & Nutrition Worker (allergen flags, dietary suitability, macronutrients).

Your job is to synthesize these two reports into a final, unified culinary verdict.
Requirements:
1. State clearly whether the proposed substitution PASSES or FAILS.
2. Incorporate the substitution worker's chemical/textural rationale.
3. Incorporate the allergen worker's safety warnings.
4. CRITICAL SAFETY RULE: If the Allergen Worker reported a 500 error / service outage, DO NOT INVENT or GUESS allergen data. Explicitly state that allergen safety could not be verified due to worker outage, and degrade to a cautious partial recommendation.
"""


def log_handoff(
    case_id: str,
    handoff_name: str,
    source: str,
    target: str,
    prompt_tokens: int,
    candidate_tokens: int,
    total_tokens: int,
    notes: str = ""
):
    """Appends structured hand-off token trace to handoffs.log."""
    entry = (
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] CASE={case_id} | "
        f"HANDOFF='{handoff_name}' | {source} -> {target} | "
        f"PROMPT_TOKENS={prompt_tokens} | CANDIDATE_TOKENS={candidate_tokens} | "
        f"TOTAL_TOKENS={total_tokens} | NOTES={notes}\n"
    )
    with open(HANDOFFS_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def run_orchestrator(
    dish_name: str,
    original_ingredient: str,
    proposed_substitution: str,
    case_id: str = "case_01",
    inject_allergen_500: bool = False
) -> Dict[str, Any]:
    """Coordinates the multi-agent squad, tracking per-hand-off tokens and synthesizing final answer."""
    client = get_gemini_client()
    overall_start = time.time()
    handoff_records = []

    # -------------------------------------------------------------
    # 1. DELEGATION 1: Orchestrator -> Substitution Worker
    # -------------------------------------------------------------
    logger.info(f"[{case_id}] Delegating to Substitution Worker...")
    sub_res = run_substitution_worker(
        dish_name=dish_name,
        original_ingredient=original_ingredient,
        proposed_substitution=proposed_substitution
    )
    log_handoff(
        case_id=case_id,
        handoff_name="orchestrator -> substitution_worker",
        source="Orchestrator",
        target="SubstitutionWorker",
        prompt_tokens=sub_res["prompt_tokens"],
        candidate_tokens=sub_res["candidate_tokens"],
        total_tokens=sub_res["total_tokens"],
        notes="Sub-task: Chemical & structural feasibility"
    )
    handoff_records.append({
        "name": "orchestrator -> substitution_worker",
        "tokens": sub_res["total_tokens"]
    })

    # -------------------------------------------------------------
    # 2. DELEGATION 2: Orchestrator -> Allergen Worker
    # -------------------------------------------------------------
    logger.info(f"[{case_id}] Delegating to Allergen Worker (inject_500={inject_allergen_500})...")
    all_res = run_allergen_worker(
        original_ingredient=original_ingredient,
        proposed_substitution=proposed_substitution,
        inject_500=inject_allergen_500
    )
    log_handoff(
        case_id=case_id,
        handoff_name="orchestrator -> allergen_worker",
        source="Orchestrator",
        target="AllergenWorker",
        prompt_tokens=all_res["prompt_tokens"],
        candidate_tokens=all_res["candidate_tokens"],
        total_tokens=all_res["total_tokens"],
        notes=f"Sub-task: Allergen & nutrition audit (status={all_res.get('status_code')})"
    )
    handoff_records.append({
        "name": "orchestrator -> allergen_worker",
        "tokens": all_res["total_tokens"]
    })

    # -------------------------------------------------------------
    # 3. SYNTHESIS: Workers -> Orchestrator (Synthesis Re-send)
    # -------------------------------------------------------------
    logger.info(f"[{case_id}] Synthesizing multi-agent specialist findings...")
    synthesis_prompt = (
        f"Original User Question / Recipe Context:\n"
        f"Dish: {dish_name}\n"
        f"Original Ingredient: {original_ingredient}\n"
        f"Proposed Substitution: {proposed_substitution}\n\n"
        f"=== REPORT FROM SUBSTITUTION SPECIALIST ===\n"
        f"{sub_res['output']}\n\n"
        f"=== REPORT FROM ALLERGEN & NUTRITION SPECIALIST ===\n"
        f"{'STATUS 500: Allergen service unavailable.' if all_res.get('status_code') == 500 else all_res['output']}\n\n"
        f"Synthesize the final authoritative culinary response."
    )

    config = types.GenerateContentConfig(
        system_instruction=SYNTHESIS_SYSTEM_INSTRUCTION,
        temperature=0.1,
    )
    syn_response = safe_generate_content(client, contents=[synthesis_prompt], config=config)

    syn_prompt_tokens = 0
    syn_candidate_tokens = 0
    if syn_response.usage_metadata:
        syn_prompt_tokens = syn_response.usage_metadata.prompt_token_count or 0
        syn_candidate_tokens = syn_response.usage_metadata.candidates_token_count or 0

    final_synthesis_text = syn_response.text or ""
    syn_total_tokens = syn_prompt_tokens + syn_candidate_tokens

    log_handoff(
        case_id=case_id,
        handoff_name="workers -> orchestrator synthesis",
        source="SpecialistWorkers",
        target="OrchestratorSynthesis",
        prompt_tokens=syn_prompt_tokens,
        candidate_tokens=syn_candidate_tokens,
        total_tokens=syn_total_tokens,
        notes="Context re-send: Full worker outputs aggregated for final synthesis"
    )
    handoff_records.append({
        "name": "workers -> orchestrator synthesis",
        "tokens": syn_total_tokens
    })

    total_duration = time.time() - overall_start
    total_multi_tokens = sub_res["total_tokens"] + all_res["total_tokens"] + syn_total_tokens
    total_cost_usd = (
        (sub_res["prompt_tokens"] + all_res["prompt_tokens"] + syn_prompt_tokens) * 0.000000075
        + (sub_res["candidate_tokens"] + all_res["candidate_tokens"] + syn_candidate_tokens) * 0.00000030
    )

    failure_behavior = None
    if inject_allergen_500:
        lower_ans = final_synthesis_text.lower()
        if "unavailable" in lower_ans or "unverified" in lower_ans or "could not be verified" in lower_ans or "500" in lower_ans or "caution" in lower_ans:
            failure_behavior = "degraded to a partial answer"
        elif any(f in lower_ans for f in ["contains no allergens", "allergen-free", "safe for tree nut allergies"]):
            failure_behavior = "lied by synthesising an allergen claim the worker never made"
        else:
            failure_behavior = "degraded to a partial answer"

    return {
        "arm": "orchestrator_squad",
        "answer": final_synthesis_text,
        "latency_s": round(total_duration, 3),
        "total_tokens": total_multi_tokens,
        "cost_usd": round(total_cost_usd, 6),
        "handoffs": handoff_records,
        "worker_outputs": {
            "substitution": sub_res["output"],
            "allergen": all_res["output"] if all_res.get("status_code") != 500 else "500_ERROR"
        },
        "failure_behavior": failure_behavior
    }
