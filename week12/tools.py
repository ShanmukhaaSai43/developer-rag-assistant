"""
=============================================================================
WEEK 12 - STEP 2: KITCHEN TOOLS CORE IMPLEMENTATION
=============================================================================
Core business logic functions called both natively and via the MCP Server:
1. search_recipes: Keyword, ingredient, and time-bounded recipe lookup
2. check_recipe_allergens: Exact-match allergen checking on structured fields
3. scale_recipe_ingredients: Mathematically scales quantities WITHOUT scaling cook times
4. get_food_safety_rule: Looks up mandatory internal cooking temperatures
5. substitute_ingredient: Performs kitchen swaps with downstream allergen checks
=============================================================================
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

DB_PATH = Path(__file__).resolve().parent / "data" / "recipes.db"

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def search_recipes(
    query: str,
    max_prep_and_cook_minutes: Optional[int] = None,
    exclude_allergens: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Search recipes by keyword, maximum total time (prep + cook), and excluded allergens.
    Always returns recipe ID, title, and explicit version tag.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query_str = f"%{query.strip().lower()}%"
    sql = """
        SELECT id, recipe_key, title, version, is_current, 
               prep_time_minutes, cook_time_minutes, base_servings, 
               ingredients_json, allergens_contains, allergens_may_contain,
               method_json, safe_internal_temp_c, reformulation_notes
        FROM recipes
        WHERE (LOWER(title) LIKE ? OR LOWER(ingredients_json) LIKE ? OR LOWER(recipe_key) LIKE ?)
    """
    cursor.execute(sql, (query_str, query_str, query_str))
    rows = cursor.fetchall()
    
    results = []
    for r in rows:
        total_time = r["prep_time_minutes"] + r["cook_time_minutes"]
        if max_prep_and_cook_minutes and total_time > max_prep_and_cook_minutes:
            continue
            
        contains_allergens = json.loads(r["allergens_contains"])
        if exclude_allergens:
            # Check if any excluded allergen is in contains
            has_conflict = any(ea.lower() in [a.lower() for a in contains_allergens] for ea in exclude_allergens)
            if has_conflict:
                continue
                
        results.append({
            "id": r["id"],
            "recipe_key": r["recipe_key"],
            "title": r["title"],
            "version": r["version"],
            "is_current": bool(r["is_current"]),
            "total_time_minutes": total_time,
            "prep_time_minutes": r["prep_time_minutes"],
            "cook_time_minutes": r["cook_time_minutes"],
            "base_servings": r["base_servings"],
            "allergens_contains": contains_allergens,
            "allergens_may_contain": json.loads(r["allergens_may_contain"]),
            "safe_internal_temp_c": r["safe_internal_temp_c"],
            "reformulation_notes": r["reformulation_notes"]
        })
    conn.close()
    return results

def check_recipe_allergens(recipe_id: str) -> Dict[str, Any]:
    """
    Exact-match allergen checker against structured declarations.
    Zero hallucination or probabilistic guessing.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, version, allergens_contains, allergens_may_contain, reformulation_notes FROM recipes WHERE id = ?", (recipe_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"error": f"Recipe ID '{recipe_id}' not found."}
        
    contains = json.loads(row["allergens_contains"])
    may_contain = json.loads(row["allergens_may_contain"])
    
    return {
        "recipe_id": row["id"],
        "title": row["title"],
        "version": row["version"],
        "contains": contains,
        "may_contain": may_contain,
        "is_nut_free": not any(a in ["tree_nuts", "peanuts"] for a in contains),
        "is_gluten_free": "gluten" not in contains,
        "is_dairy_free": "dairy" not in contains,
        "reformulation_notes": row["reformulation_notes"]
    }

def scale_recipe_ingredients(recipe_id: str, target_servings: int) -> Dict[str, Any]:
    """
    Scales ingredient weights proportionally according to target_servings / base_servings.
    CRITICAL KITCHEN SAFETY RULE:
    Bake/Cook time does NOT scale linearly! Preserves original cook time.
    """
    if target_servings <= 0:
        return {"error": "Target servings must be greater than 0."}
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, version, base_servings, cook_time_minutes, prep_time_minutes, ingredients_json, safe_internal_temp_c FROM recipes WHERE id = ?", (recipe_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"error": f"Recipe ID '{recipe_id}' not found."}
        
    base_servings = row["base_servings"]
    scale_factor = target_servings / base_servings
    original_ingredients = json.loads(row["ingredients_json"])
    
    scaled_ingredients = []
    for ing in original_ingredients:
        scaled_qty = round(ing["quantity"] * scale_factor, 1)
        scaled_ingredients.append({
            "name": ing["name"],
            "quantity": scaled_qty,
            "unit": ing["unit"]
        })
        
    return {
        "recipe_id": row["id"],
        "title": row["title"],
        "version": row["version"],
        "base_servings": base_servings,
        "target_servings": target_servings,
        "scale_factor": scale_factor,
        "scaled_ingredients": scaled_ingredients,
        "prep_time_minutes": row["prep_time_minutes"],
        "cook_time_minutes": row["cook_time_minutes"],
        "cook_time_rule": "NEVER MULTIPLY COOK/BAKE TIME. Cook time remains constant regardless of batch size.",
        "safe_internal_temp_c": row["safe_internal_temp_c"]
    }

def get_food_safety_rule(item: str) -> Dict[str, Any]:
    """
    Looks up legal food-safety minimum internal cooking temperature.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, item_name, min_internal_temp_c, min_internal_temp_f, legal_mandate 
        FROM food_safety_temps
        WHERE LOWER(item_name) LIKE ? OR LOWER(category) LIKE ?
    """, (f"%{item.lower()}%", f"%{item.lower()}%"))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"error": f"No specific food safety temperature standard found for '{item}'."}
        
    return {
        "category": row["category"],
        "item_name": row["item_name"],
        "min_internal_temp_c": row["min_internal_temp_c"],
        "min_internal_temp_f": row["min_internal_temp_f"],
        "legal_mandate": row["legal_mandate"]
    }

def substitute_ingredient(original_ingredient: str) -> Dict[str, Any]:
    """
    Looks up official substitutions from test kitchen.
    Critically tracks inherent allergens introduced by the substitute.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT original_ingredient, substitute_name, ratio, inherent_allergens, culinary_notes
        FROM substitutions
        WHERE LOWER(original_ingredient) LIKE ?
    """, (f"%{original_ingredient.lower()}%",))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return {"error": f"No approved test kitchen substitutions found for '{original_ingredient}'."}
        
    swaps = []
    for r in rows:
        swaps.append({
            "original_ingredient": r["original_ingredient"],
            "substitute_name": r["substitute_name"],
            "ratio": r["ratio"],
            "inherent_allergens": json.loads(r["inherent_allergens"]),
            "culinary_notes": r["culinary_notes"]
        })
    return {"substitutions": swaps}
