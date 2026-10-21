"""
=============================================================================
WEEK 12 - STEP 2: MCP SERVER (MODEL CONTEXT PROTOCOL)
=============================================================================
Production-grade MCP Server exposing:
- search_recipes
- check_recipe_allergens
- scale_recipe_ingredients
- get_food_safety_rule
- substitute_ingredient

Complies strictly with MCP Specification (2024-11-05):
- JSON-RPC 2.0 over stdio transport
- Stderr reserved exclusively for diagnostics & telemetry logs
- Stdout reserved exclusively for machine-parsable JSON-RPC frames
=============================================================================
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week12.tools import (
    search_recipes,
    check_recipe_allergens,
    scale_recipe_ingredients,
    get_food_safety_rule,
    substitute_ingredient
)

# Route diagnostic logging strictly to stderr
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[WEEK12-MCP] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("mcp_server")

SERVER_INFO = {
    "name": "pantry-to-plate-mcp-server",
    "version": "1.0.0"
}

TOOLS_REGISTRY = [
    {
        "name": "search_recipes",
        "description": "Search recipes in the library by keyword or dish name, with optional time limit and allergen exclusion filters. Always reports recipe ID and version tag (original vs. reformulated-2025).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword (e.g. shortbread, chicken, pasta)"},
                "max_prep_and_cook_minutes": {"type": "integer", "description": "Maximum allowed total cooking + prep time in minutes (e.g. 25)"},
                "exclude_allergens": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of allergens to strictly exclude (e.g. ['tree_nuts', 'gluten'])"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "check_recipe_allergens",
        "description": "Exact-match allergen checker on structured recipe declarations. Returns exact allergens and confirms nut-free, gluten-free, or dairy-free status without guessing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe_id": {"type": "string", "description": "Unique recipe ID (e.g. rcp_shortbread_2025 or rcp_shortbread_orig)"}
            },
            "required": ["recipe_id"]
        }
    },
    {
        "name": "scale_recipe_ingredients",
        "description": "Scales ingredient quantities by serving size. Strictly maintains constant bake/cook time (does NOT multiply cooking duration).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe_id": {"type": "string", "description": "Unique recipe ID to scale"},
                "target_servings": {"type": "integer", "description": "Desired number of servings"}
            },
            "required": ["recipe_id", "target_servings"]
        }
    },
    {
        "name": "get_food_safety_rule",
        "description": "Retrieves the mandatory minimum safe internal cooking temperature for food items (e.g. Poultry/Chicken = 74°C).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item": {"type": "string", "description": "Food category or item (e.g. chicken, poultry, pork, seafood)"}
            },
            "required": ["item"]
        }
    },
    {
        "name": "substitute_ingredient",
        "description": "Finds approved test-kitchen ingredient substitutions and reports any inherent allergens introduced by the substitute.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "original_ingredient": {"type": "string", "description": "Ingredient to substitute (e.g. Cow's Milk, Butter, All-Purpose Flour)"}
            },
            "required": ["original_ingredient"]
        }
    }
]

def handle_initialize(req_id: Any) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": SERVER_INFO,
            "capabilities": {
                "tools": {"listChanged": False}
            }
        }
    }

def handle_tools_list(req_id: Any) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "tools": TOOLS_REGISTRY
        }
    }

def handle_tools_call(req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    name = params.get("name")
    args = params.get("arguments", {})
    
    logger.info(f"Tool call invoked: {name} with args {args}")
    
    try:
        if name == "search_recipes":
            result = search_recipes(
                query=args.get("query", ""),
                max_prep_and_cook_minutes=args.get("max_prep_and_cook_minutes"),
                exclude_allergens=args.get("exclude_allergens")
            )
        elif name == "check_recipe_allergens":
            result = check_recipe_allergens(recipe_id=args.get("recipe_id", ""))
        elif name == "scale_recipe_ingredients":
            result = scale_recipe_ingredients(
                recipe_id=args.get("recipe_id", ""),
                target_servings=int(args.get("target_servings", 1))
            )
        elif name == "get_food_safety_rule":
            result = get_food_safety_rule(item=args.get("item", ""))
        elif name == "substitute_ingredient":
            result = substitute_ingredient(original_ingredient=args.get("original_ingredient", ""))
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method/Tool '{name}' not found."}
            }
            
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ],
                "isError": False
            }
        }
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": str(e)}
        }

def run_stdio_server():
    """Runs standard stdio JSON-RPC loop."""
    logger.info("Week 12 Pantry-to-Plate MCP Server started on stdio.")
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            if method == "initialize":
                res = handle_initialize(req_id)
            elif method == "tools/list":
                res = handle_tools_list(req_id)
            elif method == "tools/call":
                res = handle_tools_call(req_id, params)
            elif method == "ping":
                res = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            else:
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unrecognized method: {method}"}
                }
                
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Error parsing request line: {e}")
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    run_stdio_server()
