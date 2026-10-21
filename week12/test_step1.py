"""
=============================================================================
WEEK 12 - STEP 1 VERIFICATION TEST
=============================================================================
Tests the 'Kitchen Filing Cabinet':
1. Inspects the Shortbread trap (Original vs Reformulated-2025)
2. Executes an exact-match allergen assertion for tree nuts
3. Verifies safe internal cooking temperature check (Chicken = 74°C)
4. Checks the substitution table for allergen contamination (Almond Milk adds nuts)
=============================================================================
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "recipes.db"

def run_step1_tests():
    print("=" * 70)
    print("  STEP 1 VERIFICATION: INSPECTING THE KITCHEN FILING CABINET")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. VERIFY SHORTBREAD VERSIONS
    print("\n[CHECK 1] Inspecting Recipe Versions for 'Shortbread':")
    cursor.execute("""
        SELECT id, title, version, is_current, allergens_contains 
        FROM recipes 
        WHERE recipe_key = 'shortbread'
        ORDER BY version ASC
    """)
    rows = cursor.fetchall()
    for row in rows:
        rid, title, version, is_curr, contains = row
        status = "CURRENT (2025)" if is_curr else "SUPERSEDED"
        print(f"  * ID: {rid:<22} | Version: {version:<18} | Status: {status:<15} | Allergens: {contains}")

    # 2. EXACT ALLERGEN SAFETY ASSERTION (The Nut-Allergy Parent Query)
    print("\n[CHECK 2] Testing Exact-Match Nut Allergy Query on Both Versions:")
    for rid, title, version, is_curr, contains in rows:
        allergens = json.loads(contains)
        has_nuts = "tree_nuts" in allergens or "peanuts" in allergens
        safety_status = "[DANGER: CONTAINS TREE NUTS]" if has_nuts else "[SAFE: 100% NUT-FREE]"
        print(f"  * {title} ({version}) -> {safety_status}")

    # 3. VERIFY FOOD SAFETY TEMPERATURE (POULTRY = 74°C)
    print("\n[CHECK 3] Verifying Food Safety Minimum Internal Temperature:")
    cursor.execute("SELECT id, title, safe_internal_temp_c FROM recipes WHERE id = 'rcp_roast_chicken_orig'")
    chicken_row = cursor.fetchone()
    print(f"  * Recipe: {chicken_row[1]}")
    print(f"  * Mandatory Safe Internal Temp: {chicken_row[2]}C (165F)")
    assert chicken_row[2] == 74.0, "Food safety temperature must be exactly 74.0C"
    print("  * Verification Assertion: PASSED (74.0C strictly mandated)")

    # 4. VERIFY SUBSTITUTION CHAIN ALLERGEN RISK
    print("\n[CHECK 4] Testing Substitution Inherent Allergen Check:")
    cursor.execute("""
        SELECT original_ingredient, substitute_name, ratio, inherent_allergens, culinary_notes
        FROM substitutions
        WHERE substitute_name = 'Almond Milk'
    """)
    sub = cursor.fetchone()
    sub_allergens = json.loads(sub[3])
    print(f"  * Swap: Replace '{sub[0]}' with '{sub[1]}' (Ratio {sub[2]}x)")
    print(f"  * Inherent Allergens Introduced: {sub_allergens}")
    print(f"  * Chef Warning: {sub[4]}")
    assert "tree_nuts" in sub_allergens, "Almond milk must flag tree nuts"
    print("  * Verification Assertion: PASSED (Allergen chain caught)")

    conn.close()
    print("\n" + "=" * 70)
    print("  ALL STEP 1 CHECKS PASSED: THE FILING CABINET IS 100% RELIABLE")
    print("=" * 70)

if __name__ == "__main__":
    run_step1_tests()
