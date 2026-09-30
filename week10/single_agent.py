"""
===================================================================
WEEK 10 - ARM 1: SINGLE GENERALIST AGENT
===================================================================
A single generalist ReAct agent with access to all 5 culinary tools.
Handles decomposition, tool execution, allergen checking, and final
synthesis in a single unified prompt context.
Tracks latency, token usage (prompt + completion), and estimated cost.
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

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

from google.genai import types
from week10.gemini_client import get_gemini_client, safe_generate_content
from week10.tools import (
    search_recipes,
    scale_recipe,
    substitute_ingredient,
    get_ingredient_details,
    get_nutrition_facts
)

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[SINGLE-AGENT] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("single_agent")

TOOL_MAP = {
    "search_recipes": search_recipes,
    "scale_recipe": scale_recipe,
    "substitute_ingredient": substitute_ingredient,
    "get_ingredient_details": get_ingredient_details,
    "get_nutrition_facts": get_nutrition_facts,
}

SYSTEM_INSTRUCTION = """You are an expert culinary assistant and recipe scientist.
You have access to 5 tools:
1. `search_recipes(query)`: Search recipes in the database.
2. `scale_recipe(recipe_id, target_servings)`: Scale recipe portions.
3. `substitute_ingredient(ingredient_name, avoid_allergen)`: Find replacements to avoid an allergen.
4. `get_ingredient_details(ingredient_name)`: Lookup ingredient category, allergen flags, and shelf-life.
5. `get_nutrition_facts(ingredient_name, quantity_g)`: Lookup nutritional profile per 100g.

When answering a culinary or substitution question:
1. Evaluate whether the proposed substitution or recipe modification is chemically, textually, and culinarily viable.
2. Verify any allergen risks or dietary restrictions.
3. Clearly state whether the proposal PASSES (is viable and safe) or FAILS (leads to structural collapse, microbial death, toxic reaction, or unpalatable texture), along with your scientific rationale.
"""


def run_single_agent(question: str) -> Dict[str, Any]:
    """Runs the single generalist agent on a question and returns response + usage telemetry."""
    client = get_gemini_client()
    tools = [
        search_recipes,
        scale_recipe,
        substitute_ingredient,
        get_ingredient_details,
        get_nutrition_facts
    ]

    start_time = time.time()
    total_prompt_tokens = 0
    total_candidate_tokens = 0
    tool_calls_executed = []

    contents: List[Any] = [question]
    final_text = ""

    for step in range(5):
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
            logger.info(f"Single agent invoking tool '{name}' with args {args}")
            tool_calls_executed.append({"tool": name, "args": args})

            if name in TOOL_MAP:
                try:
                    tool_res = TOOL_MAP[name](**args)
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
        "arm": "single_agent",
        "answer": final_text,
        "latency_s": round(latency, 3),
        "prompt_tokens": total_prompt_tokens,
        "candidate_tokens": total_candidate_tokens,
        "total_tokens": total_tokens,
        "cost_usd": round(cost_usd, 6),
        "tool_calls": tool_calls_executed
    }
