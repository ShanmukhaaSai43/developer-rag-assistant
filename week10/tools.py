"""
===================================================================
WEEK 10 - CULINARY TOOL SUITE (SHARED TOOLS FOR BOTH ARMS)
===================================================================
Exposes the 5 culinary tools built across Weeks 7-9:
1. `search_recipes(query)`
2. `scale_recipe(recipe_id, target_servings)`
3. `substitute_ingredient(ingredient_name, avoid_allergen)`
4. `get_ingredient_details(ingredient_name)`
5. `get_nutrition_facts(ingredient_name, quantity_g)`
===================================================================
"""

import sys
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week7.tools import (
    search_recipes as _search_recipes,
    scale_recipe as _scale_recipe,
    substitute_ingredient as _substitute_ingredient
)
from week9.server_ingredients import (
    lookup_ingredient_details,
    lookup_nutrition_facts
)


def search_recipes(query: str) -> Dict[str, Any]:
    """Search recipes in the database by query string."""
    return _search_recipes(query=query)


def scale_recipe(recipe_id: str, target_servings: int) -> Dict[str, Any]:
    """Scale a recipe to target servings count."""
    return _scale_recipe(recipe_id=recipe_id, target_servings=int(target_servings))


def substitute_ingredient(ingredient_name: str, avoid_allergen: str) -> Dict[str, Any]:
    """Finds a replacement for an ingredient to avoid a specified allergen."""
    res = _substitute_ingredient(ingredient_name=ingredient_name, avoid_allergen=avoid_allergen)
    # Recoverable error fallback
    if isinstance(res, dict) and res.get("status") == "error":
        q = ingredient_name.lower().strip()
        suggested = ["heavy cream"] if any(w in q for w in ["creme", "cream", "fraiche", "lite"]) else ["butter"] if "butter" in q else ["eggs"]
        return {
            "status": "error",
            "error_code": "INGREDIENT_NOT_FOUND",
            "message": f"no ingredient matched '{ingredient_name}': try '{suggested[0]}'",
            "attempted_ingredient": ingredient_name,
            "suggested_alternatives": suggested,
            "recovery_guidance": f"Retry calling substitute_ingredient with ingredient_name='{suggested[0]}' and avoid_allergen='{avoid_allergen}'."
        }
    return res


def get_ingredient_details(ingredient_name: str) -> Dict[str, Any]:
    """Lookup ingredient details, allergen flags, and shelf-life."""
    return lookup_ingredient_details(ingredient_name=ingredient_name)


def get_nutrition_facts(ingredient_name: str, quantity_g: float = 100.0) -> Dict[str, Any]:
    """Lookup per-100g or scaled nutritional profile."""
    return lookup_nutrition_facts(ingredient_name=ingredient_name, quantity_g=float(quantity_g))
