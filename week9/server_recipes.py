"""
===================================================================
WEEK 9 - MCP SERVER 1: RECIPE SEARCH & SCALING SERVER
===================================================================
Standard MCP Server exposing recipe search, portion scaling, and allergen
substitution tools over stdio transport using JSON-RPC 2.0.

Adheres strictly to the MCP specification:
- Exposes tools via `tools/list`
- Executes tools via `tools/call`
- Handles `initialize` handshake
- Outputs JSON-RPC to stdout, diagnostic logs to stderr only
===================================================================
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week9.mcp_protocol import (
    MCP_PROTOCOL_VERSION,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    make_response,
    make_error_response,
    parse_message,
    serialize_message
)
from week7.tools import search_recipes, scale_recipe, substitute_ingredient
from week7.db import init_db

# Configure logger to output exclusively to stderr so stdout remains clean JSON-RPC
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[RECIPE-SERVER] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("recipe_server")


SERVER_INFO = {
    "name": "recipe-search-server",
    "version": "1.0.0"
}

SERVER_CAPABILITIES = {
    "tools": {"listChanged": False}
}

# Base definitions for Server 1's tools
TOOLS_REGISTRY = [
    {
        "name": "search_recipes",
        "description": "Search the recipe database for dishes matching a query keyword or dish title. Returns base recipes with default serving counts, ingredients list, and method.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keyword or dish title to search (e.g. 'pasta', 'salad', 'curry')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "scale_recipe",
        "description": "Calculates mathematically scaled ingredient quantities for a known recipe ID to meet a target servings count. Returns scaled quantities with exact measurements.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe_id": {
                    "type": "string",
                    "description": "The exact ID of the recipe to scale (e.g. 'rec_pasta_carbonara_001')"
                },
                "target_servings": {
                    "type": "integer",
                    "description": "Target number of servings (must be positive integer > 0)"
                }
            },
            "required": ["recipe_id", "target_servings"]
        }
    },
    {
        "name": "substitute_ingredient",
        "description": "Finds a culinary replacement for a specific ingredient to eliminate an allergen (e.g. eggs, dairy, gluten, peanuts). Returns replacement ingredient, substitution ratio, and any inherent allergens.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ingredient_name": {
                    "type": "string",
                    "description": "Exact name of the ingredient to replace (e.g. 'eggs', 'heavy cream', 'butter')"
                },
                "avoid_allergen": {
                    "type": "string",
                    "description": "Allergen to eliminate (e.g. 'eggs', 'dairy', 'gluten', 'peanuts')"
                }
            },
            "required": ["ingredient_name", "avoid_allergen"]
        }
    }
]


def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatches tool call to underlying recipe business logic."""
    if name == "search_recipes":
        query = arguments.get("query", "")
        return search_recipes(query=query)

    elif name == "scale_recipe":
        recipe_id = arguments.get("recipe_id", "")
        target_servings = int(arguments.get("target_servings", 1))
        return scale_recipe(recipe_id=recipe_id, target_servings=target_servings)

    elif name == "substitute_ingredient":
        ingredient_name = arguments.get("ingredient_name", "")
        avoid_allergen = arguments.get("avoid_allergen", "")
        return substitute_ingredient(ingredient_name=ingredient_name, avoid_allergen=avoid_allergen)

    else:
        raise ValueError(f"Unknown tool: {name}")


def handle_request(req: Dict[str, Any]) -> str:
    """Processes an incoming JSON-RPC request and returns the serialized response."""
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    logger.info(f"Incoming method: '{method}', id={req_id}")

    if method == "initialize":
        client_info = params.get("clientInfo", {})
        logger.info(f"Client initializing: {client_info}")
        res = make_response(req_id, {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": SERVER_CAPABILITIES,
            "serverInfo": SERVER_INFO
        })
        return serialize_message(res)

    elif method == "notifications/initialized":
        logger.info("Handshake confirmed by client.")
        return ""

    elif method == "ping":
        return serialize_message(make_response(req_id, {}))

    elif method == "tools/list":
        logger.info(f"Returning {len(TOOLS_REGISTRY)} registered tools.")
        res = make_response(req_id, {
            "tools": TOOLS_REGISTRY
        })
        return serialize_message(res)

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        logger.info(f"Invoking tool '{tool_name}' with args {arguments}")

        try:
            output = execute_tool(tool_name, arguments)
            is_error = isinstance(output, dict) and output.get("status") == "error"
            res = make_response(req_id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(output, indent=2)
                    }
                ],
                "isError": is_error
            })
            return serialize_message(res)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            res = make_response(req_id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"status": "error", "message": str(e)})
                    }
                ],
                "isError": True
            })
            return serialize_message(res)

    else:
        logger.warning(f"Unknown method requested: {method}")
        res = make_error_response(req_id, METHOD_NOT_FOUND, f"Method not found: {method}")
        return serialize_message(res)


def run_stdio_server():
    """Main stdio loop reading JSON-RPC lines from stdin and writing to stdout."""
    # Ensure database is primed
    init_db()
    logger.info("Recipe Search Server started on stdio transport.")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = parse_message(line)
            if not req:
                continue
            resp_str = handle_request(req)
            if resp_str:
                sys.stdout.write(resp_str)
                sys.stdout.flush()
        except Exception as e:
            logger.exception(f"Fatal error handling line: {line}")
            err = make_error_response(None, INVALID_PARAMS, f"Malformed request: {str(e)}")
            sys.stdout.write(serialize_message(err))
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
