"""
===================================================================
WEEK 8 - TRAJECTORY-INSTRUMENTED ReAct RECIPE AGENT
===================================================================
A ReAct recipe adaptation agent instrumented with complete trajectory logging.

Captures for every run:
1. `tool_sequence`: Ordered tuple/list of tools invoked.
2. `trajectory_steps`: Lap-by-lap records containing exact tool names,
   model-supplied arguments, tool observations, token counts, and costs.
3. Budget enforcement: Iterations, tokens, cost, wall-clock time.
4. Outcome payload: Final parsed JSON recipe.
===================================================================
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from google import genai
from google.genai import types
from week7.tools import TOOLS_SCHEMA, TOOL_MAPPING

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

DEFAULT_MODEL = "gemini-3.5-flash-lite"

# Model pricing for gemini-2.5-flash / flash-lite (per token)
INPUT_PRICE_PER_TOKEN = 0.075 / 1_000_000
OUTPUT_PRICE_PER_TOKEN = 0.30 / 1_000_000


def safe_generate_content(client, model: str, contents, config, max_retries: int = 5):
    """Calls Gemini with automatic exponential backoff for rate limits."""
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
                print(f"\n[RATE LIMIT 429] Waiting {wait_s}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_s)
            else:
                raise e
    raise RuntimeError("Exceeded maximum retries for Gemini API.")


AGENT_SYSTEM_PROMPT = """You are an autonomous culinary recipe adaptation agent.
Your mission:
1. Search for recipes using `search_recipes`.
2. Scale ingredient quantities to target servings using `scale_recipe`.
3. If allergen exclusions are requested, find substitutes using `substitute_ingredient`.
4. SAFETY RULE: If a substitute introduces another allergen to be avoided, call `substitute_ingredient` AGAIN on that substitute.
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
Output only the JSON block inside markdown code fences: ```json ... ```.
"""


class RecipeReActAgent:
    """ReAct recipe agent with granular trajectory tracking."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        max_iterations: int = 8,
        max_tokens: int = 25_000,
        max_cost: float = 0.05,
        wall_clock_timeout: float = 35.0,
        tools_schema: Optional[List[Dict[str, Any]]] = None,
        custom_system_prompt: Optional[str] = None
    ):
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.max_cost = max_cost
        self.wall_clock_timeout = wall_clock_timeout
        self.system_prompt = custom_system_prompt or AGENT_SYSTEM_PROMPT
        self.client = genai.Client(api_key=GEMINI_KEY)

        schema = tools_schema if tools_schema is not None else TOOLS_SCHEMA
        tool_decls = [
            types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=t["parameters"]
            )
            for t in schema
        ]
        self.tool_obj = types.Tool(function_declarations=tool_decls)

    def run(self, user_prompt: str) -> Dict[str, Any]:
        """Runs the ReAct loop, recording every tool call, argument, and lap metric."""
        start_time = time.perf_counter()

        cumulative_tokens = 0
        cumulative_cost = 0.0
        tool_sequence: List[str] = []
        trajectory_steps: List[Dict[str, Any]] = []

        conversation = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"{self.system_prompt}\nUser Request: {user_prompt}")]
            )
        ]

        current_lap = 0
        final_recipe = None
        raw_output_text = ""
        status = "completed"
        budget_fired = None

        while True:
            current_lap += 1
            lap_start = time.perf_counter()
            elapsed_time = lap_start - start_time

            # 1. Budget Checks
            if current_lap > self.max_iterations:
                status = "budget_exceeded"
                budget_fired = "max_iterations"
                break
            if cumulative_tokens >= self.max_tokens:
                status = "budget_exceeded"
                budget_fired = "max_tokens"
                break
            if cumulative_cost >= self.max_cost:
                status = "budget_exceeded"
                budget_fired = "max_cost"
                break
            if elapsed_time >= self.wall_clock_timeout:
                status = "budget_exceeded"
                budget_fired = "wall_clock_timeout"
                break

            # 2. Invoke Gemini LLM
            response = safe_generate_content(
                client=self.client,
                model=self.model_name,
                contents=conversation,
                config=types.GenerateContentConfig(
                    tools=[self.tool_obj],
                    temperature=0.0
                )
            )

            u = response.usage_metadata
            lap_in_tokens = u.prompt_token_count or 0
            lap_out_tokens = u.candidates_token_count or 0
            lap_tokens = lap_in_tokens + lap_out_tokens
            lap_cost = (lap_in_tokens * INPUT_PRICE_PER_TOKEN) + (lap_out_tokens * OUTPUT_PRICE_PER_TOKEN)

            cumulative_tokens += lap_tokens
            cumulative_cost += lap_cost

            candidate = response.candidates[0]
            conversation.append(candidate.content)

            # 3. Handle Function Calls (Trajectory Recording)
            if response.function_calls:
                for fc in response.function_calls:
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}
                    tool_sequence.append(tool_name)

                    # Execute local tool
                    tool_fn = TOOL_MAPPING.get(tool_name)
                    observation = tool_fn(**tool_args) if tool_fn else {"status": "error", "message": f"Unknown tool '{tool_name}'"}

                    # Record trajectory step
                    trajectory_steps.append({
                        "step_index": len(trajectory_steps) + 1,
                        "lap": current_lap,
                        "tool_name": tool_name,
                        "arguments": tool_args,
                        "observation": observation,
                        "lap_tokens": lap_tokens,
                        "lap_cost_usd": round(lap_cost, 7),
                        "lap_latency_s": round(time.perf_counter() - lap_start, 3)
                    })

                    # Feed tool response back into conversation
                    conversation.append(
                        types.Content(
                            role="user",
                            parts=[types.Part.from_function_response(name=tool_name, response={"result": observation})]
                        )
                    )
            else:
                # LLM produced final response
                raw_output_text = response.text or ""
                final_recipe = self._extract_json(raw_output_text)
                break

        total_latency = round(time.perf_counter() - start_time, 2)

        return {
            "status": status,
            "budget_fired": budget_fired,
            "laps_completed": current_lap,
            "latency_seconds": total_latency,
            "total_tokens": cumulative_tokens,
            "total_cost_usd": round(cumulative_cost, 6),
            "tool_sequence": tool_sequence,
            "trajectory_steps": trajectory_steps,
            "final_recipe": final_recipe,
            "raw_output_text": raw_output_text
        }

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON recipe from model output."""
        try:
            if "```json" in text:
                return json.loads(text.split("```json")[1].split("```")[0].strip())
            elif "```" in text:
                return json.loads(text.split("```")[1].split("```")[0].strip())
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end + 1])
            return json.loads(text.strip())
        except Exception:
            return None


if __name__ == "__main__":
    print("=== TESTING WEEK 8 TRAJECTORY AGENT ===")
    test_query = "Find Fettuccine Alfredo, scale it to 4 servings, and make it gluten-free."
    print(f"Query: {test_query}\n")

    agent = RecipeReActAgent()
    result = agent.run(test_query)

    print("\n=== AGENT TRAJECTORY SUMMARY ===")
    print(f"Status:        {result['status']}")
    print(f"Latency:       {result['latency_seconds']}s")
    print(f"Tokens:        {result['total_tokens']}")
    print(f"Cost:          ${result['total_cost_usd']:.6f}")
    print(f"Tool Sequence: {result['tool_sequence']}")
    print(f"Steps Count:   {len(result['trajectory_steps'])}")
    for s in result["trajectory_steps"]:
        print(f"  Step {s['step_index']}: {s['tool_name']}({s['arguments']})")
    print(f"Final Recipe:  {result['final_recipe']['title'] if result['final_recipe'] else 'None'}")
