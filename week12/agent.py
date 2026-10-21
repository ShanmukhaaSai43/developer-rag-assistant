"""
=============================================================================
WEEK 12 - STEP 3: INTEGRATED PANTRY-TO-PLATE AGENT LOOP
=============================================================================
Autonomous ReAct agent integrating:
1. Dynamic MCP tool discovery at runtime (Requirement 2)
2. Clickable citations specifying recipe ID AND version (Requirement 1)
3. Exact-match allergen safety checks and honest refusals
4. Ingredient scaling without cook time multiplication
5. Mandatory food-safety temperature enforcement (Chicken = 74°C)
6. Trajectory instrumentation capturing step-by-step tool transitions
=============================================================================
"""

import os
import sys
import time
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from google import genai
from google.genai import types
from week12.mcp_client import PantryPlateMCPClient
from week12.telemetry import TelemetryLogger

# Configure logging
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[WEEK12-AGENT] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("pantry_agent")

load_dotenv()
DEFAULT_MODEL = "gemini-3.5-flash-lite"

# Pricing for gemini-3.5-flash-lite
PRICE_PER_INPUT_TOKEN = 0.075 / 1_000_000
PRICE_PER_OUTPUT_TOKEN = 0.30 / 1_000_000

CHEF_SYSTEM_PROMPT = """You are the professional Pantry-to-Plate Kitchen Assistant for a recipe publisher.
Your role is to answer kitchen, pantry, and cooking questions accurately and safely from the library.

MANDATORY RULES:
1. CITATIONS WITH VERSIONING:
   Every recipe you recommend MUST include a citation naming both the Recipe ID AND its exact version.
   Format: `[recipe_id (version)]` (e.g. `[rcp_quick_pasta_25m (original)]` or `[rcp_shortbread_2025 (reformulated-2025)]`).
   Unversioned citations are unacceptable.

2. EXACT ALLERGEN SAFETY:
   Never guess whether a recipe is safe for allergies from memory or prose.
   Always call `check_recipe_allergens` on the recipe.
   If a user mentions an allergy (e.g., nut allergy) and a recipe contains that allergen (such as reformulated shortbread containing macadamia/walnut oil), you MUST HONESTLY REFUSE to recommend that recipe and explicitly warn the user of the anaphylaxis risk.

3. PORTION SCALING WITHOUT BURNING:
   When scaling batches, call `scale_recipe_ingredients`.
   You must explicitly remind the cook that ingredient weights scale, but BAKE/COOK TIME DOES NOT MULTIPLY.

4. FOOD SAFETY TEMPERATURES:
   When poultry or chicken is prepared, you MUST explicitly state that the meat must reach an internal temperature of 74°C (165°F) measured with a food thermometer before serving. Never omit 74°C.

5. TOOL DISCOVERY:
   Use the tools provided to inspect recipes, allergens, food safety, and substitutions.
"""

def mcp_tools_to_gemini(discovered_tools: List[Dict[str, Any]]) -> List[types.Tool]:
    """Converts MCP tool schemas into Gemini FunctionDeclarations."""
    function_decls = []
    for tool in discovered_tools:
        schema = tool.get("inputSchema", {})
        properties = {}
        for prop_name, prop_def in schema.get("properties", {}).items():
            p_type = prop_def.get("type", "string").upper()
            if p_type == "STRING":
                t_enum = types.Type.STRING
            elif p_type == "INTEGER":
                t_enum = types.Type.INTEGER
            elif p_type == "ARRAY":
                t_enum = types.Type.ARRAY
            elif p_type == "OBJECT":
                t_enum = types.Type.OBJECT
            elif p_type == "BOOLEAN":
                t_enum = types.Type.BOOLEAN
            else:
                t_enum = types.Type.STRING
                
            items_def = None
            if t_enum == types.Type.ARRAY:
                items_def = types.Schema(type=types.Type.STRING)
                
            properties[prop_name] = types.Schema(
                type=t_enum,
                description=prop_def.get("description", ""),
                items=items_def
            )
            
        function_decls.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties=properties,
                    required=schema.get("required", [])
                )
            )
        )
    return [types.Tool(function_declarations=function_decls)]

def safe_generate_content(client, model: str, contents, config, max_retries: int = 5):
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
                wait_s = 25 * (attempt + 1)
                logger.warning(f"[RATE LIMIT 429] Sleeping {wait_s}s before retry ({attempt+1}/{max_retries})...")
                time.sleep(wait_s)
            else:
                raise e
    raise RuntimeError("Max retries exceeded due to rate limits.")

class PantryToPlateAgent:
    def __init__(self, mcp_client: Optional[PantryPlateMCPClient] = None, model: str = DEFAULT_MODEL, telemetry_logger: Optional[TelemetryLogger] = None):
        self.model = model
        self.client = genai.Client()
        self.mcp_client = mcp_client or PantryPlateMCPClient()
        self.telemetry_logger = telemetry_logger or TelemetryLogger()
        self._owns_mcp = mcp_client is None
        
        # Start and discover tools at runtime
        if not self.mcp_client.process:
            self.mcp_client.start()
        self.gemini_tools = mcp_tools_to_gemini(self.mcp_client.discovered_tools)

    def run(self, user_query: str, trace_id: Optional[str] = None, max_steps: int = 5) -> Dict[str, Any]:
        if not trace_id:
            trace_id = f"tr_{uuid.uuid4().hex[:8]}"
            
        start_time = time.time()
        trajectory_steps: List[Dict[str, Any]] = []
        spans: List[Dict[str, Any]] = []
        tools_called: List[str] = []
        total_input_tokens = 0
        total_output_tokens = 0
        
        messages = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_query)]
            )
        ]
        
        config = types.GenerateContentConfig(
            system_instruction=CHEF_SYSTEM_PROMPT,
            tools=self.gemini_tools,
            temperature=0.1
        )
        
        final_answer = ""
        is_refusal = False
        
        for step_idx in range(1, max_steps + 1):
            step_start = time.time()
            resp = safe_generate_content(
                self.client,
                model=self.model,
                contents=messages,
                config=config
            )
            llm_step_lat = round((time.time() - step_start) * 1000, 2)
            
            # Token accounting
            step_in_tokens = 0
            step_out_tokens = 0
            if resp.usage_metadata:
                step_in_tokens = resp.usage_metadata.prompt_token_count or 0
                step_out_tokens = resp.usage_metadata.candidates_token_count or 0
                total_input_tokens += step_in_tokens
                total_output_tokens += step_out_tokens
                
            spans.append({
                "span_name": f"llm_step_{step_idx}",
                "trace_id": trace_id,
                "latency_ms": llm_step_lat,
                "tokens": step_in_tokens + step_out_tokens
            })
                
            if not resp.candidates or not resp.candidates[0].content:
                final_answer = "I apologize, but I could not generate a response for this request."
                break
                
            model_content = resp.candidates[0].content
            messages.append(model_content)
            
            # Check for function calls safely
            parts = model_content.parts or []
            function_calls = [p.function_call for p in parts if getattr(p, "function_call", None)]
            
            if not function_calls:
                # Agent produced final text output
                text_parts = [p.text for p in parts if getattr(p, "text", None)]
                final_answer = "\n".join(text_parts).strip()
                break
                
            # Process function calls
            for call in function_calls:
                tool_name = call.name
                tool_args = dict(call.args.items())
                tools_called.append(tool_name)
                
                tool_start = time.time()
                tool_obs = self.mcp_client.call_tool(tool_name, tool_args, trace_id=trace_id)
                tool_lat_ms = round((time.time() - tool_start) * 1000, 2)
                
                spans.append({
                    "span_name": f"mcp_tool:{tool_name}",
                    "trace_id": trace_id,
                    "latency_ms": tool_lat_ms,
                    "cost_usd": 0.00001
                })
                
                trajectory_steps.append({
                    "step": step_idx,
                    "tool": tool_name,
                    "args": tool_args,
                    "observation": tool_obs,
                    "latency_ms": tool_lat_ms
                })
                
                # Append tool observation back into conversation
                messages.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": tool_obs}
                            )
                        ]
                    )
                )

        total_latency_ms = round((time.time() - start_time) * 1000, 2)
        cost_breakdown = {
            "llm_input_usd": round(total_input_tokens * PRICE_PER_INPUT_TOKEN, 6),
            "llm_output_usd": round(total_output_tokens * PRICE_PER_OUTPUT_TOKEN, 6),
            "mcp_tools_usd": round(len(tools_called) * 0.00001, 6)
        }
        total_cost_usd = round(sum(cost_breakdown.values()), 6)
        
        # Check if output is an honest refusal
        refusal_keywords = ["cannot recommend", "not safe", "refuse", "danger", "do not serve", "allergy warning"]
        if any(kw in final_answer.lower() for kw in refusal_keywords):
            is_refusal = True
            
        # Log to telemetry
        telemetry_record = self.telemetry_logger.log_request(
            trace_id=trace_id,
            user_prompt=user_query,
            output_text=final_answer,
            spans=spans,
            token_usage={
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens
            },
            cost_breakdown=cost_breakdown
        )
            
        return {
            "trace_id": trace_id,
            "query": user_query,
            "output": final_answer,
            "is_refusal": is_refusal,
            "tools_called": tools_called,
            "tool_sequence": tuple(tools_called),
            "trajectory_steps": trajectory_steps,
            "spans": spans,
            "token_usage": {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens
            },
            "cost_breakdown": cost_breakdown,
            "cost_usd": total_cost_usd,
            "total_latency_ms": total_latency_ms,
            "telemetry_record": telemetry_record
        }

    def close(self):
        if self._owns_mcp and self.mcp_client:
            self.mcp_client.close()
