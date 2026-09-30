"""
===================================================================
WEEK 10 - SPECIALIST WORKER 1: CULINARY SUBSTITUTION WORKER
===================================================================
Specialized in culinary chemistry, gluten structure, hydration,
and recipe texture equivalence.
Constraint: Narrow prompt with ONLY the `substitute_ingredient` tool.
Tracks prompt tokens, completion tokens, latency, and tool calls.
===================================================================
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

from google.genai import types
from week10.gemini_client import get_gemini_client, safe_generate_content
from week10.tools import substitute_ingredient

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[SUB-WORKER] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("substitution_worker")

SYSTEM_INSTRUCTION = """You are a specialized Culinary Chemistry & Substitution Worker.
Your sole responsibility is evaluating whether a proposed ingredient substitution is chemically and textually viable in the specified dish.
You have access to exactly ONE tool:
- `substitute_ingredient(ingredient_name, avoid_allergen)`: Look up culinary replacements for an allergen.

Assess:
1. Structural integrity (gluten matrix, starch absorption, binders).
2. Chemical and fermentation viability (microbial viability, yeast/starter activity, pH balance).
3. Textural equivalence.
State clearly:
- Feasibility: VIABLE or NON-VIABLE
- Ratio / Technique: Any compensation required (e.g. hydration reduction)
- Chemical Rationale: Why it works or why it fails
"""


def run_substitution_worker(dish_name: str, original_ingredient: str, proposed_substitution: str) -> Dict[str, Any]:
    """Runs the specialized substitution worker on a specific substitution query."""
    client = get_gemini_client()
    tools = [substitute_ingredient]

    prompt = (
        f"Dish: {dish_name}\n"
        f"Original Ingredient: {original_ingredient}\n"
        f"Proposed Substitution: {proposed_substitution}\n\n"
        "Evaluate the culinary and chemical feasibility of this substitution."
    )

    start_time = time.time()
    total_prompt_tokens = 0
    total_candidate_tokens = 0
    tool_calls_executed = []

    contents: List[Any] = [prompt]
    final_text = ""

    for step in range(3):
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=tools,
            temperature=0.1,
        )
        response = safe_generate_content(client, contents=contents, config=config)

        if response.usage_metadata:
            total_prompt_tokens += (response.usage_metadata.prompt_token_count or 0)
            total_candidate_tokens += (response.usage_metadata.candidates_token_count or 0)

        function_calls = response.function_calls
        if not function_calls:
            final_text = response.text or ""
            break

        contents.append(response.candidates[0].content)
        for call in function_calls:
            name = call.name
            args = dict(call.args) if call.args else {}
            logger.info(f"Sub worker calling {name} with {args}")
            tool_calls_executed.append({"tool": name, "args": args})

            try:
                tool_res = substitute_ingredient(**args)
            except Exception as ex:
                tool_res = {"status": "error", "error": str(ex)}

            contents.append(
                types.Part.from_function_response(
                    name=name,
                    response={"result": tool_res}
                )
            )

    latency = time.time() - start_time
    total_tokens = total_prompt_tokens + total_candidate_tokens
    cost_usd = (total_prompt_tokens * 0.000000075) + (total_candidate_tokens * 0.00000030)

    return {
        "worker": "substitution_worker",
        "output": final_text,
        "latency_s": round(latency, 3),
        "prompt_tokens": total_prompt_tokens,
        "candidate_tokens": total_candidate_tokens,
        "total_tokens": total_tokens,
        "cost_usd": round(cost_usd, 6),
        "tool_calls": tool_calls_executed
    }
