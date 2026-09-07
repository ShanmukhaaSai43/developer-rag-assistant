"""
===================================================================
WEEK 7 - STEP 3: THE HAND-CRAFTED ReAct RECIPE AGENT
===================================================================
Features:
1. ReAct loop (Thought -> Action -> Observation -> Repeat).
2. Uses our 3 tools from Step 1 (search, scale, substitute).
3. Actively checks ALL 4 budgets on every lap:
   - max_iterations
   - max_tokens
   - max_cost
   - wall_clock_timeout
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
from week7.tools import TOOLS_SCHEMA, TOOL_MAPPING

# Load API Key
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

DEFAULT_MODEL = "gemini-3.5-flash-lite"

# Model pricing for gemini-3.5-flash-lite (per token)
INPUT_PRICE_PER_TOKEN = 0.075 / 1_000_000   # $0.075 per 1M input tokens
OUTPUT_PRICE_PER_TOKEN = 0.30 / 1_000_000   # $0.30 per 1M output tokens


def safe_generate_content(client, model: str, contents, config, max_retries: int = 5):
    """Calls Gemini with automatic retry if free-tier rate limits are reached."""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait_s = 15 * (attempt + 1)
                print(f"\n[RATE LIMIT 429] Sleeping {wait_s}s before retry ({attempt+1}/{max_retries})...")
                time.sleep(wait_s)
            else:
                raise e
    raise RuntimeError("Max retries exceeded due to rate limits.")


AGENT_SYSTEM_PROMPT = """You are an autonomous culinary recipe adaptation agent.
Your job:
1. Search for the recipe using `search_recipes`.
2. Scale the recipe to target servings using `scale_recipe`.
3. If allergen exclusions are requested, substitute offending items using `substitute_ingredient`.
4. CRITICAL SAFETY RULE: If a substitute itself introduces another allergen requested to be avoided, call `substitute_ingredient` AGAIN on that substitute to achieve a 100% safe terminal replacement.
5. When complete, output your final adapted recipe as a valid JSON object matching this schema:
{
  "title": "Recipe Name",
  "servings": 4,
  "ingredients": [
    {"name": "ingredient name", "quantity": 100.0, "unit": "g", "allergens": []}
  ],
  "method": ["step 1", "step 2"],
  "adaptation_notes": "Explanation of scaling and substitutions"
}
Output only the JSON in markdown code fence ```json ... ```.
"""


class RecipeReActAgent:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        max_iterations: int = 6,
        max_tokens: int = 20_000,
        max_cost: float = 0.05,
        wall_clock_timeout: float = 25.0
    ):
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.max_cost = max_cost
        self.wall_clock_timeout = wall_clock_timeout
        self.client = genai.Client(api_key=GEMINI_KEY)

        # Convert our tools schema to Gemini FunctionDeclarations
        tool_decls = [
            types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=t["parameters"]
            )
            for t in TOOLS_SCHEMA
        ]
        self.tool_obj = types.Tool(function_declarations=tool_decls)

    def run(self, user_prompt: str) -> Dict[str, Any]:
        """Runs the ReAct agent loop while checking all 4 budgets on every lap."""
        start_time = time.perf_counter()

        cumulative_tokens = 0
        cumulative_cost = 0.0
        laps_log = []

        conversation = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"{AGENT_SYSTEM_PROMPT}\nUser Request: {user_prompt}")]
            )
        ]

        current_lap = 0
        final_recipe = None
        status = "completed"
        budget_fired = None

        # -------------------------------------------------------------
        # THE AGENT LOOP
        # -------------------------------------------------------------
        while True:
            current_lap += 1
            elapsed_time = time.perf_counter() - start_time

            # 1. Check Budget: Iterations
            if current_lap > self.max_iterations:
                status = "budget_exceeded"
                budget_fired = "max_iterations"
                print(f"[BUDGET TRIGGERED] Hit max_iterations limit ({self.max_iterations})")
                break

            # 2. Check Budget: Tokens
            if cumulative_tokens >= self.max_tokens:
                status = "budget_exceeded"
                budget_fired = "max_tokens"
                print(f"[BUDGET TRIGGERED] Hit max_tokens limit ({self.max_tokens})")
                break

            # 3. Check Budget: Cost
            if cumulative_cost >= self.max_cost:
                status = "budget_exceeded"
                budget_fired = "max_cost"
                print(f"[BUDGET TRIGGERED] Hit max_cost limit (${self.max_cost})")
                break

            # 4. Check Budget: Wall-clock time
            if elapsed_time >= self.wall_clock_timeout:
                status = "budget_exceeded"
                budget_fired = "wall_clock_timeout"
                print(f"[BUDGET TRIGGERED] Hit wall_clock_timeout limit ({self.wall_clock_timeout}s)")
                break

            # Call LLM
            response = safe_generate_content(
                client=self.client,
                model=self.model_name,
                contents=conversation,
                config=types.GenerateContentConfig(
                    tools=[self.tool_obj],
                    temperature=0.0
                )
            )

            # Sum tokens across this lap
            u = response.usage_metadata
            lap_tokens = u.total_token_count or (u.prompt_token_count + u.candidates_token_count)
            cumulative_tokens += lap_tokens
            cumulative_cost += (u.prompt_token_count * INPUT_PRICE_PER_TOKEN) + (u.candidates_token_count * OUTPUT_PRICE_PER_TOKEN)

            candidate = response.candidates[0]
            conversation.append(candidate.content)

            # Did the AI ask to call tools?
            if response.function_calls:
                for fc in response.function_calls:
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}
                    print(f"  [LAP {current_lap}] AI called tool: {tool_name}({tool_args})")

                    # Run our Python tool from Step 1
                    tool_fn = TOOL_MAPPING.get(tool_name)
                    observation = tool_fn(**tool_args) if tool_fn else {"status": "error"}

                    # Hand tool result back to AI
                    conversation.append(
                        types.Content(
                            role="user",
                            parts=[types.Part.from_function_response(name=tool_name, response={"result": observation})]
                        )
                    )
            else:
                # The AI produced the final recipe!
                print(f"  [LAP {current_lap}] Final recipe created!")
                final_recipe = self._extract_json(response.text or "")
                break

        return {
            "status": status,
            "budget_fired": budget_fired,
            "laps_completed": current_lap,
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
    print("=== TESTING STEP 3: ReAct AGENT ===")
    test_query = "Find Peanut Butter Cookies, scale to 8 servings, and substitute egg for an egg allergy."
    print(f"User Question: '{test_query}'\n")

    agent = RecipeReActAgent(max_iterations=6)
    result = agent.run(test_query)

    print("\n=== AGENT OUTCOME ===")
    print(f"Status:          {result['status']}")
    print(f"Laps Completed:  {result['laps_completed']}")
    print(f"Time Taken:      {result['latency_seconds']} seconds")
    print(f"Total Tokens:    {result['total_tokens']}")
    print(f"Total Cost:      ${result['total_cost_usd']:.6f}")
    if result["final_recipe"]:
        print(f"Recipe Title:    {result['final_recipe'].get('title')}")
        print(f"Servings:        {result['final_recipe'].get('servings')}")
        print("Ingredients:")
        for ing in result["final_recipe"].get("ingredients", []):
            print(f"  - {ing['name']}: {ing['quantity']} {ing['unit']}")
