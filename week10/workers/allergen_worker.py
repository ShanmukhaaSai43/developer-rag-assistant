"""
===================================================================
WEEK 10 - SPECIALIST WORKER 2: ALLERGEN & NUTRITION WORKER
===================================================================
Specialized in allergen detection (FDA Big 9 allergens) and
macronutrient profile comparisons.
Constraint: Narrow prompt with ONLY `get_ingredient_details`
and `get_nutrition_facts` tools.
Supports fault injection (`inject_500=True`) to simulate third-party
worker outage for Requirement 4.
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
from week10.tools import get_ingredient_details, get_nutrition_facts

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[ALLERGEN-WORKER] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("allergen_worker")

SYSTEM_INSTRUCTION = """You are a specialized Food Allergen & Nutrition Worker.
Your sole responsibility is identifying allergen risks and nutritional differences for ingredients.
You have access to exactly TWO tools:
1. `get_ingredient_details(ingredient_name)`: Lookup allergen flags, vegan/vegetarian status, and category.
2. `get_nutrition_facts(ingredient_name, quantity_g)`: Lookup calories, protein, carbs, and fat per 100g.

Provide:
1. Allergen status: Specific allergens present (e.g. Wheat/Gluten, Dairy, Tree Nuts, Peanuts, Soy, Eggs, Fish, Shellfish, Sesame).
2. Dietary suitability: Gluten-Free, Vegan, Vegetarian.
3. Macronutrient impact: Significant shifts in protein, carbohydrates, or fat.
Be medically rigorous and conservative regarding food allergies.
"""


def run_allergen_worker(
    original_ingredient: str,
    proposed_substitution: str,
    inject_500: bool = False
) -> Dict[str, Any]:
    """Runs the allergen/nutrition specialist with optional 500 error injection."""
    # Requirement 4: Simulated 500 server failure
    if inject_500:
        logger.warning("Fault injection triggered: Simulating 500 Internal Server Error in Allergen Worker.")
        return {
            "worker": "allergen_worker",
            "status_code": 500,
            "error": "InternalServerError: 500 Nutritional & Allergen Database connection pool exhausted.",
            "output": "",
            "latency_s": 0.05,
            "prompt_tokens": 0,
            "candidate_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "tool_calls": []
        }

    client = get_gemini_client()
    tools = [get_ingredient_details, get_nutrition_facts]
    tool_map = {
        "get_ingredient_details": get_ingredient_details,
        "get_nutrition_facts": get_nutrition_facts
    }

    prompt = (
        f"Original Ingredient: {original_ingredient}\n"
        f"Proposed Substitution: {proposed_substitution}\n\n"
        "Check all allergen flags and compare nutritional profiles for both items."
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
            logger.info(f"Allergen worker calling {name} with {args}")
            tool_calls_executed.append({"tool": name, "args": args})

            if name in tool_map:
                try:
                    tool_res = tool_map[name](**args)
                except Exception as ex:
                    tool_res = {"status": "error", "error": str(ex)}
            else:
                tool_res = {"status": "error", "error": f"Unknown tool: {name}"}

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
        "worker": "allergen_worker",
        "status_code": 200,
        "output": final_text,
        "latency_s": round(latency, 3),
        "prompt_tokens": total_prompt_tokens,
        "candidate_tokens": total_candidate_tokens,
        "total_tokens": total_tokens,
        "cost_usd": round(cost_usd, 6),
        "tool_calls": tool_calls_executed
    }
