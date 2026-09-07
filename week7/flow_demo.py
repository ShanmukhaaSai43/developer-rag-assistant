"""
WEEK 7: FLOW DEMONSTRATION WITH REAL SQLITE DATABASE
===================================================
Shows how data flows from user input through our clean tools.
"""

import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from week7.types import AllergenType
from week7.tools import search_recipes, scale_recipe, substitute_ingredient

def run_demo():
    print("=" * 60)
    print("STEP 1: END-TO-END FLOW WITH REAL SQLITE DATABASE")
    print("=" * 60)

    # 1. SEARCH: Executes real SQL query against recipes.db
    print("\n1. Searching SQLite database for 'pancakes'...")
    search_res = search_recipes("pancakes")
    recipe = search_res["recipes"][0]
    print(f"   Found: {recipe['title']} (Base servings: {recipe['base_servings']})")

    # 2. SCALE: Calculates new quantities for 6 servings
    print("\n2. Scaling recipe to 6 servings...")
    scale_res = scale_recipe(recipe["id"], target_servings=6)
    print(f"   Scale Factor: {scale_res['scale_factor']}x")
    for ing in scale_res["scaled_ingredients"]:
        print(f"   - {ing['name']}: {ing['quantity']} {ing['unit']}")

    # 3. SUBSTITUTE: Queries SQLite substitutions table for dairy
    print("\n3. Finding dairy substitute for whole milk...")
    sub_res = substitute_ingredient("whole milk", AllergenType.DAIRY)
    print(f"   Original:    {sub_res['original_ingredient']}")
    print(f"   Replacement: {sub_res['replacement_ingredient']}")
    print(f"   Notes:       {sub_res['culinary_notes']}")

    print("\n" + "=" * 60)
    print("FLOW COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_demo()
