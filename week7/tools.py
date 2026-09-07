"""
===================================================================
WEEK 7 - RECIPE TOOLS (Clean & Modular)
===================================================================
Defines the 3 tools for the AI agent and fixed workflow:
1. `search_recipes`: Queries the SQLite database for recipes.
2. `scale_recipe`: Mathematically calculates scaled portions.
3. `substitute_ingredient`: Queries SQLite for safe allergen swaps.

No database clutter here! Data is cleanly managed in `week7/db.py`.
===================================================================
"""

from typing import Dict, Any, List
from week7.types import AllergenType, DietaryPreference
from week7.db import search_recipes_in_db, get_recipe_by_id, get_substitution_from_db


# ===================================================================
# 1. TOOL IMPLEMENTATIONS
# ===================================================================

def search_recipes(query: str) -> Dict[str, Any]:
    """
    Search the recipe database for dishes matching a query keyword or dish title.
    Returns base recipes with default serving counts.
    Does NOT calculate servings scaling and does NOT substitute ingredients.
    """
    matches = search_recipes_in_db(query)
    if not matches:
        return {
            "status": "error",
            "message": f"No recipes found matching query: '{query}'."
        }
    return {
        "status": "success",
        "matches_count": len(matches),
        "recipes": matches
    }


def scale_recipe(recipe_id: str, target_servings: int) -> Dict[str, Any]:
    """
    Calculates mathematically scaled ingredient quantities for a known recipe ID.
    Does NOT search recipes and does NOT substitute allergens.
    """
    base_recipe = get_recipe_by_id(recipe_id)
    if not base_recipe:
        return {
            "status": "error",
            "message": f"Recipe ID '{recipe_id}' not found in database."
        }
    
    if target_servings <= 0:
        return {
            "status": "error",
            "message": f"target_servings must be a positive integer, got {target_servings}."
        }

    base_servings = base_recipe["base_servings"]
    scale_factor = target_servings / base_servings
    
    scaled_ingredients = []
    for ing in base_recipe["ingredients"]:
        scaled_ingredients.append({
            "name": ing["name"],
            "quantity": round(ing["quantity"] * scale_factor, 2),
            "unit": ing["unit"],
            "allergens": ing["allergens"]
        })

    return {
        "status": "success",
        "recipe_id": recipe_id,
        "title": base_recipe["title"],
        "base_servings": base_servings,
        "target_servings": target_servings,
        "scale_factor": scale_factor,
        "scaled_ingredients": scaled_ingredients,
        "method": base_recipe["method"]
    }


def substitute_ingredient(ingredient_name: str, avoid_allergen: AllergenType) -> Dict[str, Any]:
    """
    Finds a culinary replacement for a specific ingredient to eliminate an allergen.
    Returns replacement ingredient, ratio, and any allergens in the substitute.
    Does NOT search the recipe catalog and does NOT scale portions.
    """
    allergen_val = avoid_allergen.value if isinstance(avoid_allergen, AllergenType) else str(avoid_allergen).lower().strip()
    
    # Normalize common singular words to match plural enums
    singular_map = {
        "egg": "eggs",
        "peanut": "peanuts",
        "tree_nut": "tree_nuts",
        "tree nut": "tree_nuts",
        "nut": "tree_nuts",
        "nuts": "tree_nuts"
    }
    allergen_val = singular_map.get(allergen_val, allergen_val)
    
    sub = get_substitution_from_db(ingredient_name, allergen_val)
    if sub:
        return {
            "status": "success",
            "original_ingredient": ingredient_name,
            "avoided_allergen": allergen_val,
            "replacement_ingredient": sub["substitute_name"],
            "quantity_ratio": sub["ratio"],
            "inherent_allergens": sub["inherent_allergens"],
            "culinary_notes": sub["culinary_notes"]
        }
    
    return {
        "status": "error",
        "message": f"No verified substitute found in database for '{ingredient_name}' avoiding '{allergen_val}'."
    }


# ===================================================================
# 2. TOOL SCHEMAS FOR THE AI
# ===================================================================

TOOLS_SCHEMA = [
    {
        "name": "search_recipes",
        "description": "Search the recipe database for dishes matching a dish name or ingredient keyword. Returns base recipes with default serving counts. Does NOT perform scaling or substitutions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The dish name or main ingredient to search for, e.g. 'peanut butter cookies' or 'alfredo'."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "scale_recipe",
        "description": "Calculates scaled ingredient quantities for a known recipe ID to match target servings. Does NOT search recipes or replace ingredients.",
        "parameters": {
            "type": "object",
            "properties": {
                "recipe_id": {
                    "type": "string",
                    "description": "The unique identifier of the recipe, e.g. 'rec_pb_cookies'."
                },
                "target_servings": {
                    "type": "integer",
                    "description": "The desired number of servings to scale the recipe to (must be > 0)."
                }
            },
            "required": ["recipe_id", "target_servings"]
        }
    },
    {
        "name": "substitute_ingredient",
        "description": "Recommends a verified culinary substitute for an ingredient to eliminate an allergen. Returns replacement item, ratio, and any allergens present in the substitute. Does NOT search or scale recipes.",
        "parameters": {
            "type": "object",
            "properties": {
                "ingredient_name": {
                    "type": "string",
                    "description": "The name of the ingredient that contains the allergen, e.g. 'peanut butter' or 'heavy cream'."
                },
                "avoid_allergen": {
                    "type": "string",
                    "enum": [a.value for a in AllergenType if a != AllergenType.NONE],
                    "description": "The specific allergen category to eliminate from the recipe."
                }
            },
            "required": ["ingredient_name", "avoid_allergen"]
        }
    }
]

TOOL_MAPPING = {
    "search_recipes": search_recipes,
    "scale_recipe": scale_recipe,
    "substitute_ingredient": substitute_ingredient
}
