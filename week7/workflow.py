"""
===================================================================
WEEK 7 - STEP 4: DETERMINISTIC FIXED WORKFLOW (NO LOOPS)
===================================================================
Executes the identical recipe adaptation task as a hard-coded sequence:
1. Step 1: `search_recipes`
2. Step 2: `scale_recipe`
3. Step 3: `substitute_ingredient`
4. Step 4: Final LLM synthesis to format output JSON.

Same tools, same model, same output schema. Zero loops.
===================================================================
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from google import genai
from google.genai import types
from week7.tools import search_recipes, scale_recipe, substitute_ingredient
from week7.agent import safe_generate_content, INPUT_PRICE_PER_TOKEN, OUTPUT_PRICE_PER_TOKEN

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
DEFAULT_MODEL = "gemini-3.5-flash-lite"

WORKFLOW_EXTRACTION_PROMPT = """Extract the recipe adaptation parameters from this user request.
Return ONLY a valid JSON object with:
{
  "dish_query": "dish name to search",
  "target_servings": 4,
  "allergen_to_avoid": "peanuts",  // MUST be one of: "peanuts", "tree_nuts", "dairy", "gluten", "eggs", "soy", "sesame"
  "ingredient_to_replace": "peanut butter"
}
"""

WORKFLOW_SYNTHESIS_PROMPT = """You are a culinary chef assistant.
Given the scaled recipe and the ingredient substitution result below, output the final adapted recipe.
IMPORTANT:
- If a substitution result is provided, replace the original ingredient in the ingredients list with the replacement ingredient (multiplying quantity by quantity_ratio), and update allergens.
- Keep all other scaled ingredients intact.

You MUST output ONLY a valid JSON object matching this schema:
{
  "title": "Recipe Name",
  "servings": 4,
  "ingredients": [
    {"name": "ingredient name", "quantity": 100.0, "unit": "g", "allergens": []}
  ],
  "method": ["step 1", "step 2"],
  "adaptation_notes": "Explanation of scaling and substitutions performed"
}
Output only the JSON in markdown code fence ```json ... ```.
"""


class RecipeFixedWorkflow:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.client = genai.Client(api_key=GEMINI_KEY)

    def run(self, user_prompt: str) -> Dict[str, Any]:
        """Runs the fixed 3-step pipeline without an agent loop."""
        start_time = time.perf_counter()
        cumulative_tokens = 0
        cumulative_cost = 0.0

        # -------------------------------------------------------------
        # STEP 0: Parse User Parameters (Single LLM Call)
        # -------------------------------------------------------------
        parse_resp = safe_generate_content(
            client=self.client,
            model=self.model_name,
            contents=f"{WORKFLOW_EXTRACTION_PROMPT}\nUser Request: {user_prompt}",
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json"
            )
        )
        u0 = parse_resp.usage_metadata
        t0 = u0.total_token_count or (u0.prompt_token_count + u0.candidates_token_count)
        cumulative_tokens += t0
        cumulative_cost += (u0.prompt_token_count * INPUT_PRICE_PER_TOKEN) + (u0.candidates_token_count * OUTPUT_PRICE_PER_TOKEN)

        try:
            params = json.loads(parse_resp.text)
        except Exception:
            params = {"dish_query": user_prompt, "target_servings": 4, "allergen_to_avoid": "", "ingredient_to_replace": ""}

        dish_query = params.get("dish_query", "")
        target_servings = params.get("target_servings", 4)
        allergen = params.get("allergen_to_avoid", "")
        ing_to_replace = params.get("ingredient_to_replace", "")

        # -------------------------------------------------------------
        # STEP 1: Search Base Recipe (Direct Python Tool Call)
        # -------------------------------------------------------------
        search_res = search_recipes(query=dish_query)
        if search_res.get("status") != "success" or not search_res.get("recipes"):
            return {
                "status": "failed_at_step_1",
                "latency_seconds": round(time.perf_counter() - start_time, 2),
                "total_tokens": cumulative_tokens,
                "total_cost_usd": round(cumulative_cost, 6),
                "final_recipe": None
            }

        selected_recipe = search_res["recipes"][0]
        recipe_id = selected_recipe["id"]

        # -------------------------------------------------------------
        # STEP 2: Scale Recipe (Direct Python Tool Call)
        # -------------------------------------------------------------
        scale_res = scale_recipe(recipe_id=recipe_id, target_servings=int(target_servings))
        if scale_res.get("status") != "success":
            return {
                "status": "failed_at_step_2",
                "latency_seconds": round(time.perf_counter() - start_time, 2),
                "total_tokens": cumulative_tokens,
                "total_cost_usd": round(cumulative_cost, 6),
                "final_recipe": None
            }

        # -------------------------------------------------------------
        # STEP 3: Substitute Single Allergen (Direct Python Tool Call)
        # -------------------------------------------------------------
        if not ing_to_replace:
            for ing in scale_res.get("scaled_ingredients", []):
                if allergen in [a.lower() for a in ing.get("allergens", [])]:
                    ing_to_replace = ing["name"]
                    break

        sub_res = None
        if ing_to_replace and allergen:
            sub_res = substitute_ingredient(ingredient_name=ing_to_replace, avoid_allergen=allergen)

        # -------------------------------------------------------------
        # STEP 4: Final Format Synthesis (Single LLM Call)
        # -------------------------------------------------------------
        synthesis_input = f"""{WORKFLOW_SYNTHESIS_PROMPT}

Scaled Recipe:
{json.dumps(scale_res, indent=2)}

Substitution Information:
{json.dumps(sub_res, indent=2) if sub_res else "No substitution applied."}

User Request: {user_prompt}
"""
        synth_resp = safe_generate_content(
            client=self.client,
            model=self.model_name,
            contents=synthesis_input,
            config=types.GenerateContentConfig(temperature=0.0)
        )
        u1 = synth_resp.usage_metadata
        t1 = u1.total_token_count or (u1.prompt_token_count + u1.candidates_token_count)
        cumulative_tokens += t1
        cumulative_cost += (u1.prompt_token_count * INPUT_PRICE_PER_TOKEN) + (u1.candidates_token_count * OUTPUT_PRICE_PER_TOKEN)

        final_recipe = self._extract_json(synth_resp.text)
        return {
            "status": "completed",
            "latency_seconds": round(time.perf_counter() - start_time, 2),
            "total_tokens": cumulative_tokens,
            "total_cost_usd": round(cumulative_cost, 6),
            "final_recipe": final_recipe
        }

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            if "```json" in text:
                return json.loads(text.split("```json")[1].split("```")[0].strip())
            elif "```" in text:
                return json.loads(text.split("```")[1].split("```")[0].strip())
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
            return json.loads(text.strip())
        except Exception:
            return None


if __name__ == "__main__":
    print("=== TESTING STEP 4: FIXED WORKFLOW ===")
    test_query = "Find Peanut Butter Cookies, scale to 8 servings, and substitute egg for an egg allergy."
    print(f"User Question: '{test_query}'\n")

    workflow = RecipeFixedWorkflow()
    result = workflow.run(test_query)

    print("=== WORKFLOW OUTCOME ===")
    print(f"Status:          {result['status']}")
    print(f"Time Taken:      {result['latency_seconds']} seconds")
    print(f"Total Tokens:    {result['total_tokens']}")
    print(f"Total Cost:      ${result['total_cost_usd']:.6f}")
    if result["final_recipe"]:
        print(f"Recipe Title:    {result['final_recipe'].get('title')}")
        print(f"Servings:        {result['final_recipe'].get('servings')}")
        print("Ingredients:")
        for ing in result["final_recipe"].get("ingredients", []):
            print(f"  - {ing['name']}: {ing['quantity']} {ing['unit']}")
