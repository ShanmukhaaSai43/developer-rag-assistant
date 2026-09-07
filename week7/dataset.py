"""
===================================================================
WEEK 7 - STEP 2: THE 10 BENCHMARK EXAM QUESTIONS
===================================================================
To race the AI Agent against the Fixed Workflow fairly, we give both
systems the exact same 10 requests:
- 7 Standard linear requests (Search -> Scale -> 1 Swap)
- 3 Cascading requests (The substitute contains an allergen, forcing a 2nd swap)
===================================================================
"""

from typing import List, Dict, Any

BENCHMARK_REQUESTS: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # 7 STANDARD (EASY / LINEAR) QUESTIONS
    # -------------------------------------------------------------
    {
        "id": "req_01",
        "type": "standard",
        "query": "Find Fettuccine Alfredo, scale it to 4 servings, and make it gluten-free.",
        "dish_name": "alfredo",
        "target_servings": 4,
        "avoid_allergens": ["gluten"],
        "expected_substitutes": ["gluten-free corn fettuccine"]
    },
    {
        "id": "req_02",
        "type": "standard",
        "query": "Find Classic Peanut Butter Cookies, scale it to 8 servings, and substitute the egg for an egg allergy.",
        "dish_name": "peanut butter cookies",
        "target_servings": 8,
        "avoid_allergens": ["eggs"],
        "expected_substitutes": ["flax egg (1 tbsp ground flax + 3 tbsp water)"]
    },
    {
        "id": "req_03",
        "type": "standard",
        "query": "Find Honey Nut Breakfast Granola, scale to 12 servings, and make it nut-free by substituting almonds.",
        "dish_name": "granola",
        "target_servings": 12,
        "avoid_allergens": ["tree_nuts"],
        "expected_substitutes": ["pumpkin seeds"]
    },
    {
        "id": "req_04",
        "type": "standard",
        "query": "Find Fluffy Banana Pancakes, scale to 6 servings, and substitute whole milk to make it dairy-free.",
        "dish_name": "banana pancakes",
        "target_servings": 6,
        "avoid_allergens": ["dairy"],
        "expected_substitutes": ["unsweetened oat milk"]
    },
    {
        "id": "req_05",
        "type": "standard",
        "query": "Find Genovese Basil Pesto Pasta, scale it to 2 servings, and make it gluten-free.",
        "dish_name": "pesto",
        "target_servings": 2,
        "avoid_allergens": ["gluten"],
        "expected_substitutes": ["brown rice spaghetti"]
    },
    {
        "id": "req_06",
        "type": "standard",
        "query": "Find Fettuccine Alfredo, scale to 6 servings, and substitute the butter for a dairy allergy.",
        "dish_name": "alfredo",
        "target_servings": 6,
        "avoid_allergens": ["dairy"],
        "expected_substitutes": ["vegan plant butter"]
    },
    {
        "id": "req_07",
        "type": "standard",
        "query": "Find Fluffy Banana Pancakes, scale to 9 servings, and make it gluten-free by substituting the flour.",
        "dish_name": "banana pancakes",
        "target_servings": 9,
        "avoid_allergens": ["gluten"],
        "expected_substitutes": ["1-to-1 gluten-free baking blend"]
    },

    # -------------------------------------------------------------
    # 3 CASCADING (TRICK / DYNAMIC) QUESTIONS
    # -------------------------------------------------------------
    {
        "id": "req_08",
        "type": "cascade",
        "query": "Find Classic Peanut Butter Cookies, scale to 4 servings. The diner has a severe peanut allergy AND a tree nut allergy, so replace peanut butter with something safe from both.",
        "dish_name": "peanut butter cookies",
        "target_servings": 4,
        "avoid_allergens": ["peanuts", "tree_nuts"],
        "intermediate_allergen_sub": "almond butter",       # Contains tree_nuts! (Forbidden)
        "terminal_safe_sub": "sunflower seed butter"        # Safe! (Required)
    },
    {
        "id": "req_09",
        "type": "cascade",
        "query": "Find Fettuccine Alfredo, scale to 4 servings. I am allergic to dairy AND tree nuts. Adapt the heavy cream so it is strictly free of both dairy and nuts.",
        "dish_name": "alfredo",
        "target_servings": 4,
        "avoid_allergens": ["dairy", "tree_nuts"],
        "intermediate_allergen_sub": "almond milk creamer", # Contains tree_nuts! (Forbidden)
        "terminal_safe_sub": "canned coconut cream"         # Safe! (Required)
    },
    {
        "id": "req_10",
        "type": "cascade",
        "query": "Find Cold Sesame Peanut Noodles, scale to 4 servings. I have both a sesame allergy AND a peanut allergy. Replace the sesame oil safely with an oil free of both.",
        "dish_name": "sesame noodles",
        "target_servings": 4,
        "avoid_allergens": ["sesame", "peanuts"],
        "intermediate_allergen_sub": "toasted peanut oil",  # Contains peanuts! (Forbidden)
        "terminal_safe_sub": "perilla seed oil"             # Safe! (Required)
    }
]


# ===================================================================
# THE AUTOMATIC GRADER (Evaluator)
# ===================================================================

def evaluate_recipe(request_case: Dict[str, Any], final_recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grades whether the adapted recipe passed or failed.
    Checks:
    1. Did it make the correct number of servings?
    2. Are any of the forbidden allergens present?
    3. In trick/cascade cases, did it use the terminal safe substitute?
    """
    errors = []

    if not final_recipe or not isinstance(final_recipe, dict):
        return {"passed": False, "errors": ["No recipe returned."]}

    # Check 1: Servings count
    actual_servings = final_recipe.get("servings")
    if actual_servings != request_case["target_servings"]:
        errors.append(f"Wanted {request_case['target_servings']} servings, got {actual_servings}")

    # Check 2: Ingredients & Allergens
    ingredients = final_recipe.get("ingredients", [])
    if not ingredients:
        errors.append("No ingredients list in recipe.")
    else:
        ingredient_names = [i.get("name", "").lower() for i in ingredients]
        all_allergens = []
        for i in ingredients:
            all_allergens.extend([a.lower() for a in i.get("allergens", [])])

        # Are any forbidden allergens present?
        for forbidden in request_case["avoid_allergens"]:
            if forbidden.lower() in all_allergens:
                errors.append(f"Allergy Violation: Contains forbidden allergen '{forbidden}'")

        # For cascade cases, make sure the intermediate allergen wasn't kept!
        if request_case["type"] == "cascade":
            intermediate = request_case["intermediate_allergen_sub"].lower()
            terminal = request_case["terminal_safe_sub"].lower()

            if intermediate in ingredient_names:
                errors.append(f"Cascade Failure: Intermediate allergen '{intermediate}' was kept!")
            if terminal not in ingredient_names:
                errors.append(f"Cascade Failure: Did not reach safe substitute '{terminal}'")

    passed = (len(errors) == 0)
    return {
        "passed": passed,
        "errors": errors
    }


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print(f"Total benchmark questions loaded: {len(BENCHMARK_REQUESTS)}")
    standard_count = sum(1 for r in BENCHMARK_REQUESTS if r["type"] == "standard")
    cascade_count = sum(1 for r in BENCHMARK_REQUESTS if r["type"] == "cascade")
    print(f"  - Standard (linear) questions: {standard_count}")
    print(f"  - Cascading (trick) questions: {cascade_count}")
