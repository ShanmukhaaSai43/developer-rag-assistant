"""
===================================================================
WEEK 9 - MCP SERVER 2: INGREDIENT & NUTRITION DATABASE SERVER
===================================================================
Stood up by the Content Team over the centralized ingredient database.
Exposes tools via standard MCP (JSON-RPC 2.0 over stdio transport):
1. `get_ingredient_details`: Lookup by ingredient name, allergen flags, and shelf-life.
2. `get_nutrition_facts`: Per-100g nutritional profile (calories, protein, carbs, fat, fiber).

Compliance:
- Standard MCP protocol version: 2024-11-05
- Logging strictly directed to stderr
- Output formatted as single-line JSON-RPC on stdout
===================================================================
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

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

# Route diagnostic logging strictly to stderr to prevent stdio stream corruption
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[INGREDIENT-SERVER] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ingredient_server")


SERVER_INFO = {
    "name": "ingredient-database-server",
    "version": "1.1.0",
    "vendor": "Content Team / Nutrition Service"
}

SERVER_CAPABILITIES = {
    "tools": {"listChanged": False}
}

# In-memory Content Team Ingredient Knowledge Base
INGREDIENT_DATABASE: Dict[str, Dict[str, Any]] = {
    "heavy cream": {
        "canonical_name": "Heavy Cream",
        "category": "Dairy",
        "allergen_flags": ["dairy", "lactose"],
        "is_vegan": False,
        "is_vegetarian": True,
        "is_gluten_free": True,
        "storage": "Refrigerate at 2-4°C, consume within 7 days of opening",
        "nutrition_per_100g": {
            "calories_kcal": 345,
            "protein_g": 2.1,
            "carbohydrates_g": 2.8,
            "fat_g": 37.0,
            "fiber_g": 0.0,
            "sodium_mg": 38.0
        }
    },
    "coconut cream": {
        "canonical_name": "Coconut Cream",
        "category": "Plant-based dairy alternative",
        "allergen_flags": ["tree_nuts"],  # FDA classifies coconut as tree nut
        "is_vegan": True,
        "is_vegetarian": True,
        "is_gluten_free": True,
        "storage": "Store in cool dry pantry; once opened, refrigerate up to 5 days",
        "nutrition_per_100g": {
            "calories_kcal": 330,
            "protein_g": 3.6,
            "carbohydrates_g": 7.0,
            "fat_g": 34.7,
            "fiber_g": 2.2,
            "sodium_mg": 15.0
        }
    },
    "butter": {
        "canonical_name": "Unsalted Butter",
        "category": "Dairy",
        "allergen_flags": ["dairy", "lactose"],
        "is_vegan": False,
        "is_vegetarian": True,
        "is_gluten_free": True,
        "storage": "Refrigerate at 4°C",
        "nutrition_per_100g": {
            "calories_kcal": 717,
            "protein_g": 0.9,
            "carbohydrates_g": 0.1,
            "fat_g": 81.1,
            "fiber_g": 0.0,
            "sodium_mg": 11.0
        }
    },
    "olive oil": {
        "canonical_name": "Extra Virgin Olive Oil",
        "category": "Oils & Fats",
        "allergen_flags": [],
        "is_vegan": True,
        "is_vegetarian": True,
        "is_gluten_free": True,
        "storage": "Store in dark bottle away from heat and direct sunlight",
        "nutrition_per_100g": {
            "calories_kcal": 884,
            "protein_g": 0.0,
            "carbohydrates_g": 0.0,
            "fat_g": 100.0,
            "fiber_g": 0.0,
            "sodium_mg": 2.0
        }
    },
    "parmesan cheese": {
        "canonical_name": "Parmigiano-Reggiano",
        "category": "Hard Aged Cheese",
        "allergen_flags": ["dairy"],
        "is_vegan": False,
        "is_vegetarian": False,  # Traditional animal rennet
        "is_gluten_free": True,
        "storage": "Wrap in parchment paper, refrigerate at 3-6°C",
        "nutrition_per_100g": {
            "calories_kcal": 431,
            "protein_g": 38.5,
            "carbohydrates_g": 4.1,
            "fat_g": 28.6,
            "fiber_g": 0.0,
            "sodium_mg": 1529.0
        }
    },
    "nutritional yeast": {
        "canonical_name": "Nutritional Yeast Flakes",
        "category": "Seasoning / Plant-based Cheese Alternative",
        "allergen_flags": [],
        "is_vegan": True,
        "is_vegetarian": True,
        "is_gluten_free": True,
        "storage": "Store in airtight jar in cool dark pantry",
        "nutrition_per_100g": {
            "calories_kcal": 380,
            "protein_g": 51.0,
            "carbohydrates_g": 36.0,
            "fat_g": 4.0,
            "fiber_g": 27.0,
            "sodium_mg": 105.0
        }
    },
    "fettuccine": {
        "canonical_name": "Durum Wheat Fettuccine",
        "category": "Dry Pasta",
        "allergen_flags": ["gluten", "wheat"],
        "is_vegan": True,
        "is_vegetarian": True,
        "is_gluten_free": False,
        "storage": "Store dry in sealed container",
        "nutrition_per_100g": {
            "calories_kcal": 355,
            "protein_g": 12.5,
            "carbohydrates_g": 73.0,
            "fat_g": 1.5,
            "fiber_g": 3.2,
            "sodium_mg": 6.0
        }
    },
    "eggs": {
        "canonical_name": "Large Grade A Eggs",
        "category": "Poultry / Eggs",
        "allergen_flags": ["eggs"],
        "is_vegan": False,
        "is_vegetarian": True,
        "is_gluten_free": True,
        "storage": "Refrigerate below 4°C",
        "nutrition_per_100g": {
            "calories_kcal": 143,
            "protein_g": 12.6,
            "carbohydrates_g": 0.7,
            "fat_g": 9.5,
            "fiber_g": 0.0,
            "sodium_mg": 142.0
        }
    }
}


TOOLS_REGISTRY = [
    {
        "name": "get_ingredient_details",
        "description": "Lookup official ingredient specifications by ingredient name. Exposes comprehensive allergen flags, food category, and storage instructions from the content team's ingredient database.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ingredient_name": {
                    "type": "string",
                    "description": "The common or culinary name of the ingredient (e.g. 'heavy cream', 'coconut cream', 'parmesan cheese')"
                }
            },
            "required": ["ingredient_name"]
        }
    },
    {
        "name": "get_nutrition_facts",
        "description": "Retrieves verified nutritional profile (calories, protein, carbs, fat, fiber, sodium) per 100g or scaled to specified quantity in grams.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ingredient_name": {
                    "type": "string",
                    "description": "Name of the ingredient to query nutrition for"
                },
                "quantity_g": {
                    "type": "number",
                    "description": "Optional quantity in grams to calculate total nutrients for (defaults to 100g)"
                }
            },
            "required": ["ingredient_name"]
        }
    }
]


def normalize_ingredient_key(name: str) -> str:
    """Normalizes input ingredient name for robust dictionary lookup."""
    clean = name.strip().lower()
    # Normalize common singular/plural or descriptors
    if clean.endswith("s") and clean not in INGREDIENT_DATABASE and clean[:-1] in INGREDIENT_DATABASE:
        return clean[:-1]
    return clean


def lookup_ingredient_details(ingredient_name: str) -> Dict[str, Any]:
    """Retrieves ingredient specification and allergen profile."""
    key = normalize_ingredient_key(ingredient_name)
    if key not in INGREDIENT_DATABASE:
        return {
            "status": "error",
            "message": f"Ingredient '{ingredient_name}' not found in the content team ingredient database.",
            "available_samples": list(INGREDIENT_DATABASE.keys())[:5]
        }

    data = INGREDIENT_DATABASE[key]
    return {
        "status": "success",
        "canonical_name": data["canonical_name"],
        "category": data["category"],
        "allergen_flags": data["allergen_flags"],
        "is_vegan": data["is_vegan"],
        "is_vegetarian": data["is_vegetarian"],
        "is_gluten_free": data["is_gluten_free"],
        "storage": data["storage"]
    }


def lookup_nutrition_facts(ingredient_name: str, quantity_g: float = 100.0) -> Dict[str, Any]:
    """Calculates macro and micronutrients per 100g or scaled to quantity_g."""
    key = normalize_ingredient_key(ingredient_name)
    if key not in INGREDIENT_DATABASE:
        return {
            "status": "error",
            "message": f"Ingredient '{ingredient_name}' not found in nutritional database.",
            "available_samples": list(INGREDIENT_DATABASE.keys())[:5]
        }

    if quantity_g <= 0:
        return {
            "status": "error",
            "message": f"quantity_g must be greater than zero, got {quantity_g}"
        }

    base_nutrition = INGREDIENT_DATABASE[key]["nutrition_per_100g"]
    multiplier = quantity_g / 100.0

    scaled = {
        k: round(v * multiplier, 2)
        for k, v in base_nutrition.items()
    }

    return {
        "status": "success",
        "ingredient": INGREDIENT_DATABASE[key]["canonical_name"],
        "quantity_g": round(quantity_g, 2),
        "nutrition": scaled,
        "is_per_100g_standard": quantity_g == 100.0
    }


def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatches tool call to appropriate business logic handler."""
    if name == "get_ingredient_details":
        ing_name = arguments.get("ingredient_name", "")
        return lookup_ingredient_details(ing_name)

    elif name == "get_nutrition_facts":
        ing_name = arguments.get("ingredient_name", "")
        qty = float(arguments.get("quantity_g", 100.0))
        return lookup_nutrition_facts(ing_name, qty)

    else:
        raise ValueError(f"Unknown tool on Ingredient Server: {name}")


def handle_request(req: Dict[str, Any]) -> str:
    """Processes incoming JSON-RPC request."""
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    logger.info(f"Incoming method: '{method}', id={req_id}")

    if method == "initialize":
        logger.info(f"Client initializing with params: {params.get('clientInfo')}")
        res = make_response(req_id, {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": SERVER_CAPABILITIES,
            "serverInfo": SERVER_INFO
        })
        return serialize_message(res)

    elif method == "notifications/initialized":
        logger.info("Initialized notification received.")
        return ""

    elif method == "ping":
        return serialize_message(make_response(req_id, {}))

    elif method == "tools/list":
        logger.info(f"Returning {len(TOOLS_REGISTRY)} tools from ingredient database.")
        res = make_response(req_id, {
            "tools": TOOLS_REGISTRY
        })
        return serialize_message(res)

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        logger.info(f"Executing tool '{tool_name}' with args: {arguments}")

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
        logger.warning(f"Method not found: {method}")
        res = make_error_response(req_id, METHOD_NOT_FOUND, f"Method not found: {method}")
        return serialize_message(res)


def run_stdio_server():
    """Stdio event loop."""
    logger.info("Ingredient Database MCP Server running on stdio transport.")
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
            logger.exception(f"Error handling message: {line}")
            err = make_error_response(None, INVALID_PARAMS, f"Malformed request: {str(e)}")
            sys.stdout.write(serialize_message(err))
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
