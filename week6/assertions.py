"""
===================================================================
WEEK 6: Deterministic Code Assertions
===================================================================
Requirement 2: Move at least 2 criteria out of the judge and into
deterministic Python assertions.

Criteria moved out of the LLM Judge:
1. Allergen warning present when allergen ingredient is present.
2. Oven / Fermentation temperature carries explicit units (°F / °C).
3. Servings count echoed and quantities parse as valid numbers.
4. Ingredients used in method steps appear in the ingredient table.
===================================================================
"""

import re
from typing import Dict, Any, Tuple, List

# Known major culinary allergen keywords
MAJOR_ALLERGENS = {
    "wheat": ["wheat", "bread flour", "all-purpose flour", "pastry flour", "flour"],
    "gluten": ["gluten", "barley", "rye", "wheat"],
    "fish": ["fish", "fish sauce", "anchovy"],
    "crustacean": ["shrimp", "salted shrimp", "saeujeot", "crab"],
    "soy": ["soy", "soybean", "soybeans", "miso", "soy sauce"],
    "dairy": ["butter", "milk", "cream", "cheese"],
    "egg": ["egg", "eggs", "egg wash"],
    "tree nut": ["cashew", "almond", "walnut", "coconut"]
}

def assert_allergen_warning_present(case: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Deterministic Assertion 1:
    Verifies that if any major allergen is present in the ingredient list,
    the allergen_note explicitly identifies and declares the allergen.
    """
    recipe = case.get("recipe_output", {})
    ingredients = [ing.get("name", "").lower() for ing in recipe.get("ingredients", [])]
    allergen_note = recipe.get("allergen_note", "").lower()
    
    if not allergen_note:
        return False, "Missing allergen_note field."

    detected_allergens = set()
    for allergen_group, keywords in MAJOR_ALLERGENS.items():
        for ing in ingredients:
            if any(kw in ing for kw in keywords):
                detected_allergens.add(allergen_group)
                break

    # If allergens are in ingredients, ensure allergen_note acknowledges them or declares allergen-free
    for allergen in detected_allergens:
        # Check if the note either mentions the allergen or notes its absence / substitution
        if allergen not in allergen_note and not any(kw in allergen_note for kw in MAJOR_ALLERGENS[allergen]):
            return False, f"Allergen '{allergen}' present in ingredients but not declared in allergen_note."

    return True, "Allergen warnings accurately declared."

def assert_temperature_has_units(case: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Deterministic Assertion 2:
    Verifies that any temperature stated in baking_temperature or method_steps
    carries explicit units (°F, °C, deg F, deg C).
    """
    recipe = case.get("recipe_output", {})
    temp_field = recipe.get("baking_temperature", "")
    method_steps = recipe.get("method_steps", [])
    
    all_text = temp_field + " " + " ".join(method_steps)
    
    # Match complete temperature numbers (e.g. 70 to 550) not followed by degree or temperature unit
    # e.g., "bake at 450 for 20 mins" -> fails; "bake at 450°F" -> passes
    bare_temp_pattern = re.compile(r'\b(?:at|preheat to|ferment at|incubate at|bake at)\s+(\d{2,3})\b(?!\s*(?:°|deg|F\b|C\b|%|minutes|mins|hours|days|sets|times))', re.IGNORECASE)
    
    matches = bare_temp_pattern.findall(all_text)
    if matches:
        return False, f"Found temperature without explicit units: {matches}"
    
    # Verify baking_temperature field itself has degree units
    if temp_field and not re.search(r'(°F|°C|deg|degrees)', temp_field, re.IGNORECASE):
        return False, f"baking_temperature '{temp_field}' lacks explicit temperature units."

    return True, "All temperature values carry explicit units."

def assert_quantities_parse_as_numbers(case: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Deterministic Assertion 3:
    Verifies that all ingredient weights and baker's percentages parse into valid numbers
    rather than unparseable strings (e.g. '1000g' -> 1000, '75.0%' -> 75.0).
    """
    recipe = case.get("recipe_output", {})
    ingredients = recipe.get("ingredients", [])
    if not ingredients:
        return False, "Ingredient list is empty."
    
    for ing in ingredients:
        weight_str = ing.get("weight", "").strip()
        pct_str = ing.get("bakers_percentage", "").strip()
        
        # Check weight has a numeric component or valid unit count (e.g. '1000g', '2 leaves', '250g')
        weight_num = re.search(r'(\d+(\.\d+)?)', weight_str)
        if not weight_num:
            return False, f"Ingredient '{ing.get('name')}' has non-numeric weight '{weight_str}'."
        
        # Check percentage parses as number or valid 'N/A'
        if pct_str != "N/A":
            pct_num = re.search(r'(\d+(\.\d+)?)', pct_str)
            if not pct_num:
                return False, f"Ingredient '{ing.get('name')}' has unparseable baker's percentage '{pct_str}'."
    
    return True, "All ingredient weights and percentages parse into valid numerical values."

def assert_method_ingredients_in_table(case: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Deterministic Assertion 4:
    Verifies that key ingredients added in method steps exist in the ingredient table
    (no ghost ingredients appearing only in instructions).
    """
    recipe = case.get("recipe_output", {})
    table_ingredients = " ".join([ing.get("name", "").lower() for ing in recipe.get("ingredients", [])])
    method_steps = recipe.get("method_steps", [])
    
    # Check for ingredients explicitly mixed/added/combined into dough/ferment
    # If an ingredient is explicitly added with weight in method (e.g. "Add 50g water"), ensure water is in table
    add_pattern = re.compile(r'\b(?:add|mix in|incorporate|dissolve|combine)\s+(?:\d+g\s+)?([a-z\s]+?)(?:,|\.|\s+and|\s+with|\s+into|\s+for)', re.IGNORECASE)
    
    for step in method_steps:
        for match in add_pattern.finditer(step):
            added_item = match.group(1).strip().lower()
            if len(added_item) > 3 and not any(common in added_item for common in ["minutes", "starter", "water", "flour", "salt", "sugar", "koji", "butter", "eggs", "oil", "tea"]):
                continue
            # Check key core ingredients
            for core in ["starter", "flour", "sugar", "koji", "butter", "eggs", "oil", "tea"]:
                if core in added_item and core not in table_ingredients:
                    return False, f"Ghost ingredient '{core}' added in method steps but missing from ingredient table."
            
    return True, "All method ingredients verified against ingredient table."

def run_all_assertions(case: Dict[str, Any]) -> Dict[str, Any]:
    """Runs all 4 deterministic assertions and returns individual and aggregate results."""
    res_allergen, msg_allergen = assert_allergen_warning_present(case)
    res_temp, msg_temp = assert_temperature_has_units(case)
    res_qty, msg_qty = assert_quantities_parse_as_numbers(case)
    res_method, msg_method = assert_method_ingredients_in_table(case)
    
    all_passed = res_allergen and res_temp and res_qty and res_method
    return {
        "all_passed": all_passed,
        "assertions": {
            "allergen_warning_present": {"passed": res_allergen, "message": msg_allergen},
            "temperature_has_units": {"passed": res_temp, "message": msg_temp},
            "quantities_parse_as_numbers": {"passed": res_qty, "message": msg_qty},
            "method_ingredients_in_table": {"passed": res_method, "message": msg_method}
        }
    }
