"""
===================================================================
WEEK 8 - DATASET & TRAJECTORY GROUND TRUTH SPECIFICATION
===================================================================
Defines the 10 benchmark recipe cases for trajectory evaluation.

REQUIREMENT 1 COMPLIANCE:
Asserts expected tool sequences for all 10 recipe cases.
Explicitly documents why cases legitimately accept more than one valid path
(e.g., commutative property of scaling before vs. after ingredient substitution)
and asserts those valid paths as a SET of tuples, avoiding brittle over-assertion.
===================================================================
"""

from typing import List, Dict, Any, Set, Tuple


BENCHMARK_CASES: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # 7 STANDARD CASES (Optimal: 3 Steps)
    # Search -> Scale -> Substitute  OR  Search -> Substitute -> Scale
    # -------------------------------------------------------------
    {
        "id": "req_01",
        "type": "standard",
        "query": "Find Fettuccine Alfredo, scale it to 4 servings, and make it gluten-free.",
        "dish_name": "alfredo",
        "recipe_id": "rec_creamy_alfredo",
        "target_servings": 4,
        "avoid_allergens": ["gluten"],
        "target_ingredient_to_swap": "fettuccine pasta",
        "expected_terminal_substitute": "gluten-free corn fettuccine",
        "optimal_steps": 3,
        "accepts_alternate_paths": True,
        "alternate_path_rationale": (
            "Commutative ordering: Scaling portions to 4 servings before finding the gluten-free "
            "substitute vs. finding the gluten-free substitute before scaling yields mathematically "
            "and culinarily identical results."
        ),
        "valid_tool_sequences": {
            ("search_recipes", "scale_recipe", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "scale_recipe")
        }
    },
    {
        "id": "req_02",
        "type": "standard",
        "query": "Find Classic Peanut Butter Cookies, scale it to 8 servings, and substitute the egg for an egg allergy.",
        "dish_name": "peanut butter cookies",
        "recipe_id": "rec_pb_cookies",
        "target_servings": 8,
        "avoid_allergens": ["eggs"],
        "target_ingredient_to_swap": "egg",
        "expected_terminal_substitute": "flax egg (1 tbsp ground flax + 3 tbsp water)",
        "optimal_steps": 3,
        "accepts_alternate_paths": True,
        "alternate_path_rationale": (
            "Commutative ordering: Scaling cookie yield to 8 servings before or after substituting "
            "the binder (egg -> flax egg) produces the exact same adapted recipe."
        ),
        "valid_tool_sequences": {
            ("search_recipes", "scale_recipe", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "scale_recipe")
        }
    },
    {
        "id": "req_03",
        "type": "standard",
        "query": "Find Honey Nut Breakfast Granola, scale to 12 servings, and make it nut-free by substituting almonds.",
        "dish_name": "granola",
        "recipe_id": "rec_nutty_granola",
        "target_servings": 12,
        "avoid_allergens": ["tree_nuts"],
        "target_ingredient_to_swap": "almonds",
        "expected_terminal_substitute": "pumpkin seeds",
        "optimal_steps": 3,
        "accepts_alternate_paths": True,
        "alternate_path_rationale": (
            "Commutative ordering: Multiplying batch weight to 12 servings prior to swapping almonds "
            "with pumpkin seeds is equally valid to swapping the ingredient first and scaling the batch second."
        ),
        "valid_tool_sequences": {
            ("search_recipes", "scale_recipe", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "scale_recipe")
        }
    },
    {
        "id": "req_04",
        "type": "standard",
        "query": "Find Fluffy Banana Pancakes, scale to 6 servings, and substitute whole milk to make it dairy-free.",
        "dish_name": "banana pancakes",
        "recipe_id": "rec_banana_pancakes",
        "target_servings": 6,
        "avoid_allergens": ["dairy"],
        "target_ingredient_to_swap": "whole milk",
        "expected_terminal_substitute": "unsweetened oat milk",
        "optimal_steps": 3,
        "accepts_alternate_paths": True,
        "alternate_path_rationale": (
            "Commutative ordering: Whether the liquid volume is scaled to 6 servings before or after "
            "replacing whole milk with oat milk does not affect final composition."
        ),
        "valid_tool_sequences": {
            ("search_recipes", "scale_recipe", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "scale_recipe")
        }
    },
    {
        "id": "req_05",
        "type": "standard",
        "query": "Find Genovese Basil Pesto Pasta, scale it to 2 servings, and make it gluten-free.",
        "dish_name": "pesto",
        "recipe_id": "rec_classic_pesto",
        "target_servings": 2,
        "avoid_allergens": ["gluten"],
        "target_ingredient_to_swap": "spaghetti",
        "expected_terminal_substitute": "brown rice spaghetti",
        "optimal_steps": 3,
        "accepts_alternate_paths": True,
        "alternate_path_rationale": (
            "Commutative ordering: Halving pasta weight to 2 servings before substituting spaghetti "
            "with brown rice spaghetti vs. swapping pasta and then downscaling are both correct."
        ),
        "valid_tool_sequences": {
            ("search_recipes", "scale_recipe", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "scale_recipe")
        }
    },
    {
        "id": "req_06",
        "type": "standard",
        "query": "Find Fettuccine Alfredo, scale to 6 servings, and substitute the butter for a dairy allergy.",
        "dish_name": "alfredo",
        "recipe_id": "rec_creamy_alfredo",
        "target_servings": 6,
        "avoid_allergens": ["dairy"],
        "target_ingredient_to_swap": "butter",
        "expected_terminal_substitute": "vegan plant butter",
        "optimal_steps": 3,
        "accepts_alternate_paths": True,
        "alternate_path_rationale": (
            "Commutative ordering: Scaling butter weight to 6 servings before swapping for vegan plant butter "
            "vs. swapping butter first and scaling are equally valid culinary trajectories."
        ),
        "valid_tool_sequences": {
            ("search_recipes", "scale_recipe", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "scale_recipe")
        }
    },
    {
        "id": "req_07",
        "type": "standard",
        "query": "Find Fluffy Banana Pancakes, scale to 9 servings, and make it gluten-free by substituting the flour.",
        "dish_name": "banana pancakes",
        "recipe_id": "rec_banana_pancakes",
        "target_servings": 9,
        "avoid_allergens": ["gluten"],
        "target_ingredient_to_swap": "all-purpose flour",
        "expected_terminal_substitute": "1-to-1 gluten-free baking blend",
        "optimal_steps": 3,
        "accepts_alternate_paths": True,
        "alternate_path_rationale": (
            "Commutative ordering: Scaling flour to 9 servings before swapping for 1-to-1 gluten-free blend "
            "vs. swapping flour first and then calculating 9 servings are equivalent valid paths."
        ),
        "valid_tool_sequences": {
            ("search_recipes", "scale_recipe", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "scale_recipe")
        }
    },

    # -------------------------------------------------------------
    # 3 CASCADING CASES (Optimal: 4 Steps)
    # Search -> Scale -> Swap1 -> Swap2 (or Scale interspersed)
    # The intermediate substitution introduces a secondary allergen!
    # -------------------------------------------------------------
    {
        "id": "req_08",
        "type": "cascade",
        "query": (
            "Find Classic Peanut Butter Cookies, scale to 4 servings. The diner has a severe peanut allergy "
            "AND a tree nut allergy, so replace peanut butter with something safe from both."
        ),
        "dish_name": "peanut butter cookies",
        "recipe_id": "rec_pb_cookies",
        "target_servings": 4,
        "avoid_allergens": ["peanuts", "tree_nuts"],
        "target_ingredient_to_swap": "peanut butter",
        "intermediate_allergen_sub": "almond butter",       # Introduces tree_nuts!
        "expected_terminal_substitute": "sunflower seed butter", # 100% safe
        "optimal_steps": 4,
        "accepts_alternate_paths": True,
        "alternate_path_rationale": (
            "Commutative ordering in multi-step swaps: Scaling can occur immediately after search, "
            "between the first and second substitution, or after both substitutions are resolved."
        ),
        "valid_tool_sequences": {
            ("search_recipes", "scale_recipe", "substitute_ingredient", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "scale_recipe", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "substitute_ingredient", "scale_recipe")
        }
    },
    {
        "id": "req_09",
        "type": "cascade",
        "query": (
            "Find Fettuccine Alfredo, scale to 4 servings. I am allergic to dairy AND tree nuts. "
            "Adapt the heavy cream so it is strictly free of both dairy and nuts."
        ),
        "dish_name": "alfredo",
        "recipe_id": "rec_creamy_alfredo",
        "target_servings": 4,
        "avoid_allergens": ["dairy", "tree_nuts"],
        "target_ingredient_to_swap": "heavy cream",
        "intermediate_allergen_sub": "almond milk creamer", # Introduces tree_nuts!
        "expected_terminal_substitute": "canned coconut cream",  # 100% safe
        "optimal_steps": 4,
        "accepts_alternate_paths": True,
        "alternate_path_rationale": (
            "Commutative ordering in multi-step swaps: Scaling recipe portions can legitimately occur "
            "before any swaps, between intermediate swap and terminal swap, or after both swaps."
        ),
        "valid_tool_sequences": {
            ("search_recipes", "scale_recipe", "substitute_ingredient", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "scale_recipe", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "substitute_ingredient", "scale_recipe")
        }
    },
    {
        "id": "req_10",
        "type": "cascade",
        "query": (
            "Find Cold Sesame Peanut Noodles, scale to 4 servings. I have both a sesame allergy "
            "AND a peanut allergy. Replace the sesame oil safely with an oil free of both."
        ),
        "dish_name": "sesame noodles",
        "recipe_id": "rec_sesame_noodles",
        "target_servings": 4,
        "avoid_allergens": ["sesame", "peanuts"],
        "target_ingredient_to_swap": "sesame oil",
        "intermediate_allergen_sub": "toasted peanut oil",  # Introduces peanuts!
        "expected_terminal_substitute": "perilla seed oil",  # 100% safe
        "optimal_steps": 4,
        "accepts_alternate_paths": True,
        "alternate_path_rationale": (
            "Commutative ordering in multi-step swaps: Scaling portions can legitimately happen at "
            "step 2, step 3, or step 4, as long as both sesame oil -> toasted peanut oil -> perilla seed oil "
            "substitutions are completed."
        ),
        "valid_tool_sequences": {
            ("search_recipes", "scale_recipe", "substitute_ingredient", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "scale_recipe", "substitute_ingredient"),
            ("search_recipes", "substitute_ingredient", "substitute_ingredient", "scale_recipe")
        }
    }
]


def evaluate_outcome(case: Dict[str, Any], final_recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grades the final output recipe against culinary outcome specifications:
    1. Servings count accuracy
    2. Zero presence of forbidden allergens in ingredients
    3. Proper terminal substitute reached (and intermediate allergen not retained in cascades)
    """
    errors = []

    if not final_recipe or not isinstance(final_recipe, dict):
        return {"passed": False, "errors": ["Missing or invalid recipe JSON output."]}

    # Check 1: Target Servings
    actual_servings = final_recipe.get("servings")
    if actual_servings != case["target_servings"]:
        errors.append(f"Servings mismatch: Wanted {case['target_servings']}, got {actual_servings}")

    ingredients = final_recipe.get("ingredients", [])
    if not ingredients:
        errors.append("Empty ingredients list in final recipe.")
        return {"passed": False, "errors": errors}

    ingredient_names = [str(i.get("name", "")).lower() for i in ingredients]
    all_allergens = []
    for i in ingredients:
        all_allergens.extend([str(a).lower() for a in i.get("allergens", [])])

    # Check 2: Avoid Allergens
    for forbidden in case["avoid_allergens"]:
        if forbidden.lower() in all_allergens:
            errors.append(f"Allergen violation: Contains prohibited allergen '{forbidden}'")

    # Check 3: Terminal safe substitute
    terminal_expected = case["expected_terminal_substitute"].lower()
    if not any(terminal_expected in name for name in ingredient_names):
        errors.append(f"Substitute missing: Expected terminal safe substitute '{terminal_expected}'")

    # Check 4: Cascade intermediate check
    if case["type"] == "cascade":
        intermediate = case["intermediate_allergen_sub"].lower()
        if any(intermediate in name for name in ingredient_names):
            errors.append(f"Cascade failure: Intermediate allergen item '{intermediate}' was kept!")

    return {
        "passed": len(errors) == 0,
        "errors": errors
    }


if __name__ == "__main__":
    print(f"Total benchmark cases loaded: {len(BENCHMARK_CASES)}")
    for case in BENCHMARK_CASES:
        paths = len(case["valid_tool_sequences"])
        print(f"  [{case['id']}] {case['type'].upper()}: {paths} valid trajectory path(s)")
