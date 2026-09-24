"""
===================================================================
WEEK 9 - DYNAMIC MCP-DISCOVERY RECIPE REACT AGENT
===================================================================
An autonomous culinary ReAct agent that discovers ALL capabilities
dynamically over Model Context Protocol (MCP).

Key Architectural Principles:
1. ZERO hardcoded tools: All tools are discovered at runtime from
   configured MCP servers via `tools/list`.
2. Pure config-driven: Adding, removing, or swapping servers requires
   ZERO code changes in this module.
3. Full trajectory tracing: Tracks server provenance, tool calls,
   arguments, and execution results for auditability.
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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from google import genai
from google.genai import types
from week9.mcp_client import MCPClientManager

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

DEFAULT_MODEL = "gemini-3.5-flash-lite"

# Model pricing estimation (per token)
INPUT_PRICE_PER_TOKEN = 0.075 / 1_000_000
OUTPUT_PRICE_PER_TOKEN = 0.30 / 1_000_000

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[RECIPE-AGENT] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("recipe_agent")


def safe_generate_content(client, model: str, contents, config, max_retries: int = 4):
    """Executes Gemini content generation with exponential backoff on rate limits."""
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
                wait_s = 10 * (attempt + 1)
                logger.warning(f"Rate limited (429). Retrying in {wait_s}s...")
                time.sleep(wait_s)
            else:
                raise e
    raise RuntimeError("Exceeded maximum retries for Gemini API.")


DEFAULT_SYSTEM_PROMPT = """You are an autonomous culinary recipe adaptation and analysis agent.
All your tools are dynamically discovered via Model Context Protocol (MCP) servers.

Operational Instructions:
1. Use `search_recipes` to find matching dishes.
2. Use `scale_recipe` when target servings are specified.
3. Use `substitute_ingredient` when allergen avoidance is requested.
4. If a tool returns an error or no match, adapt your query once. As soon as you have the necessary recipe information, DO NOT make redundant calls—output your complete final culinary answer and stop calling tools.
"""


class MCPRecipeReActAgent:
    """ReAct agent powered exclusively by dynamic MCP tool discovery."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        model_name: str = DEFAULT_MODEL,
        max_iterations: int = 10,
        max_tokens: int = 35_000,
        wall_clock_timeout: float = 60.0,
        system_prompt: Optional[str] = None
    ):
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.wall_clock_timeout = wall_clock_timeout
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

        # Initialize MCP Client Manager with config
        self.config_path = config_path or (Path(__file__).resolve().parent / "mcp_servers.json")
        self.mcp_manager = MCPClientManager(config_path=self.config_path)

        # Dynamic connection & discovery
        logger.info(f"Loading MCP servers from {self.config_path}")
        self.mcp_manager.load_and_connect()

        # Build dynamic tool declarations from discovered MCP tools
        self.discovered_tools_report = self.mcp_manager.get_discovered_tools_report()
        logger.info(f"Dynamically discovered {self.discovered_tools_report['total_count']} tools: {self.discovered_tools_report['tool_names']}")

        self.function_declarations = self.mcp_manager.get_gemini_function_declarations()
        self.tool_obj = types.Tool(function_declarations=self.function_declarations) if self.function_declarations else None

        # Gemini Client
        self.client = genai.Client(api_key=GEMINI_KEY)

    def run(self, user_prompt: str) -> Dict[str, Any]:
        """
        Executes the ReAct loop dynamically invoking tools via MCP.
        Records full trajectory including server provenance for every tool call.
        """
        start_time = time.perf_counter()
        cumulative_tokens = 0
        cumulative_cost = 0.0
        tool_sequence: List[str] = []
        trajectory_steps: List[Dict[str, Any]] = []

        conversation = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"{self.system_prompt}\n\nUser Request: {user_prompt}")]
            )
        ]

        current_lap = 0
        status = "completed"
        final_answer = ""

        while True:
            current_lap += 1
            elapsed_time = time.perf_counter() - start_time

            if current_lap > self.max_iterations:
                status = "budget_exceeded:max_iterations"
                break
            if elapsed_time >= self.wall_clock_timeout:
                status = "budget_exceeded:timeout"
                break

            gen_config = types.GenerateContentConfig(
                tools=[self.tool_obj] if self.tool_obj else [],
                temperature=0.0
            )

            response = safe_generate_content(
                client=self.client,
                model=self.model_name,
                contents=conversation,
                config=gen_config
            )

            # Track tokens & cost
            usage = response.usage_metadata
            input_tokens = getattr(usage, "prompt_token_count", 0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0
            lap_tokens = input_tokens + output_tokens
            cumulative_tokens += lap_tokens
            lap_cost = (input_tokens * INPUT_PRICE_PER_TOKEN) + (output_tokens * OUTPUT_PRICE_PER_TOKEN)
            cumulative_cost += lap_cost

            # Check for tool calls
            candidate = response.candidates[0] if response.candidates else None
            if not candidate or not candidate.content or not candidate.content.parts:
                status = "empty_model_response"
                break

            tool_calls = [p.function_call for p in candidate.content.parts if p.function_call]

            # Append assistant message to conversation history
            conversation.append(candidate.content)

            if not tool_calls:
                # Model produced final answer
                final_answer = "".join([p.text for p in candidate.content.parts if p.text])
                break

            # Execute tool calls via MCP client
            response_parts = []
            for call in tool_calls:
                t_name = call.name
                t_args = dict(call.args) if call.args else {}
                tool_sequence.append(t_name)

                # Dispatch via MCP Client
                obs_text, is_err, s_name = self.mcp_manager.call_tool(t_name, t_args)

                step_record = {
                    "lap": current_lap,
                    "tool": t_name,
                    "server": s_name,
                    "arguments": t_args,
                    "observation": obs_text,
                    "is_error": is_err,
                    "lap_tokens": lap_tokens,
                    "lap_cost": round(lap_cost, 6)
                }
                trajectory_steps.append(step_record)

                response_parts.append(
                    types.Part.from_function_response(
                        name=t_name,
                        response={"result": obs_text}
                    )
                )

            # Feed observation back into conversation
            conversation.append(
                types.Content(
                    role="user",
                    parts=response_parts
                )
            )

        total_duration = time.perf_counter() - start_time

        return {
            "status": status,
            "user_prompt": user_prompt,
            "final_answer": final_answer,
            "tool_sequence": tool_sequence,
            "trajectory_steps": trajectory_steps,
            "metrics": {
                "total_laps": current_lap,
                "cumulative_tokens": cumulative_tokens,
                "cumulative_cost": round(cumulative_cost, 6),
                "duration_seconds": round(total_duration, 3)
            },
            "discovered_tools": self.discovered_tools_report
        }

    def close(self):
        """Releases all MCP server connections and resources."""
        self.mcp_manager.close()
