"""
===================================================================
WEEK 10 - SHARED EVALUATION JUDGE
===================================================================
Judges both the Single Agent and Multi-Agent Orchestrator answers
against the exact Week-6 ground-truth human labels in `labels_25.json`.
Criterion: Culinary Chemical Viability & Textural Equivalence.
Returns: 1 (PASS) if verdict matches ground truth, 0 (FAIL) if hallucinated or wrong.
===================================================================
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

from google.genai import types
from week10.gemini_client import get_gemini_client, safe_generate_content

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[JUDGE] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("judge")

JUDGE_PROMPT_TEMPLATE = """You are a senior culinary scientist evaluating an AI agent's answer against human ground-truth.

### EVALUATION CRITERION
Assess whether the agent's answer accurately captures culinary chemical viability, fermentation survival, and structural integrity.

### TEST CASE
- Dish: {dish_name}
- Original Ingredient: {original_ingredient}
- Proposed Substitution: {proposed_substitution}
- Human Ground Truth Label: {human_label} ({ground_truth_desc})
- Human Ground Truth Rationale: {human_rationale}

### AGENT ANSWER UNDER TEST
{agent_answer}

### JUDGMENT TASK
Does the agent's answer align with ground truth?
- If Ground Truth is PASS (1), did the agent recognize it as viable with appropriate compensations?
- If Ground Truth is FAIL (0), did the agent correctly reject it or identify structural/microbial failure?

Respond strictly with a JSON object:
{{
  "verdict": 1 or 0,
  "rationale": "one sentence explanation"
}}
"""


def judge_answer(
    dish_name: str,
    original_ingredient: str,
    proposed_substitution: str,
    human_label: int,
    human_rationale: str,
    agent_answer: str
) -> Dict[str, Any]:
    """Evaluates agent response against ground truth label."""
    client = get_gemini_client()
    ground_truth_desc = "VIABLE / PASS" if human_label == 1 else "NON-VIABLE / COLLAPSE / FAIL"

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        dish_name=dish_name,
        original_ingredient=original_ingredient,
        proposed_substitution=proposed_substitution,
        human_label=human_label,
        ground_truth_desc=ground_truth_desc,
        human_rationale=human_rationale,
        agent_answer=agent_answer
    )

    try:
        config = types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json"
        )
        response = safe_generate_content(client, contents=[prompt], config=config)
        res_text = response.text.strip()
        if res_text.startswith("```json"):
            res_text = res_text[7:]
        if res_text.endswith("```"):
            res_text = res_text[:-3]
        data = json.loads(res_text.strip())
        return {
            "verdict": int(data.get("verdict", 0)),
            "rationale": data.get("rationale", "")
        }
    except Exception as e:
        logger.warning(f"Judge model error: {e}. Using deterministic fallback.")

    # Deterministic fallback check based on keywords if LLM judge unreachable
    lower_ans = agent_answer.lower()
    if human_label == 0:
        passed = any(w in lower_ans for w in ["fail", "not viable", "non-viable", "cannot substitute", "ruin", "collapse", "unworkable", "toxic"])
    else:
        passed = any(w in lower_ans for w in ["pass", "viable", "can substitute", "acceptable", "works well", "maintain"])
    return {
        "verdict": 1 if passed else 0,
        "rationale": "Keyword heuristic fallback judgment"
    }
