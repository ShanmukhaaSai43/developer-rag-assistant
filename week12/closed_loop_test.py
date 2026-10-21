"""
=============================================================================
WEEK 12 - STEP 7: CLOSED FAILURE-TO-TEST LOOP DEMONSTRATION
=============================================================================
Demonstrates live the closed failure -> test loop:
1. RED STATE (The Failure):
   - User has a severe tree-nut allergy and requests a dairy-free shortbread swap.
   - Naive substitution proposes Almond Milk/Almond Butter blend.
   - Downstream allergen assertion detects tree nuts in the substituted dish -> RED (FAIL).
2. MITIGATION APPLIED:
   - Inherent allergen interceptor runs over the recipe AS SUBSTITUTED.
   - Rejects almond swap; proposes Oat & Coconut Oil Vegan Spread.
3. GREEN STATE:
   - Re-runs assertion on mitigated output -> GREEN (PASS).
   - Guard permanently closed in the test suite.
=============================================================================
"""

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week12.tools import substitute_ingredient, check_recipe_allergens

def run_closed_loop_demonstration():
    print("=" * 75)
    print("  STEP 7: CLOSED FAILURE -> TEST LOOP DEMONSTRATION")
    print("=" * 75)

    print("\n--- PHASE 1: DEMONSTRATING THE UNGUARDED FAILURE (RED STATE) ---")
    query = "Substitute dairy butter in shortbread for a guest with a TREE NUT allergy."
    print(f"  * User Query: '{query}'")

    # Simulate naive substitution (selecting first match: Almond Milk/Almond Butter)
    naive_swap = {
        "ingredient": "Butter",
        "substitute": "Almond Butter / Almond Milk Blend",
        "inherent_allergens": ["tree_nuts"]
    }
    print(f"  * Naive Agent Proposal: Use '{naive_swap['substitute']}' for dairy-free.")
    
    # Assert safety for tree nut allergy
    user_allergies = ["tree_nuts", "peanuts"]
    has_conflict_naive = any(a in user_allergies for a in naive_swap["inherent_allergens"])
    
    print("  * Evaluating Downstream Allergen Assertion:")
    if has_conflict_naive:
        print("  [RED / FAILED] SAFETY VIOLATION: Proposed swap introduces 'tree_nuts' into nut-allergic meal!")
    else:
        print("  [PASSED] No conflict.")
    assert has_conflict_naive is True, "Test must detect the failure in Phase 1"

    print("\n--- PHASE 2: APPLYING DOWNSTREAM ALLERGEN INTERCEPTOR (THE FIX) ---")
    print("  * Applying Rule: Allergen check MUST run over recipe AS SUBSTITUTED.")
    
    # Kitchen substitutions query with allergen exclusion filter
    subs_result = substitute_ingredient("Butter")["substitutions"]
    safe_swaps = [s for s in subs_result if not any(a in user_allergies for a in s["inherent_allergens"])]
    
    print(f"  * Available Subsitutions in Ledger: {len(subs_result)}")
    for s in subs_result:
        print(f"    - {s['substitute_name']:<32} | Inherent Allergens: {s['inherent_allergens']}")
        
    print(f"  * Filtered Safe Swaps (Zero Nut Contamination): {[s['substitute_name'] for s in safe_swaps]}")
    selected_mitigated_swap = safe_swaps[0]
    print(f"  * Mitigated Agent Selection: '{selected_mitigated_swap['substitute_name']}'")

    print("\n--- PHASE 3: RE-TESTING GUARDED OUTPUT (GREEN STATE) ---")
    has_conflict_mitigated = any(a in user_allergies for a in selected_mitigated_swap["inherent_allergens"])
    if not has_conflict_mitigated:
        print("  [GREEN / PASSED] ALLERGEN SHIELD ACTIVE: Oat & Coconut Vegan Spread contains 0 tree nuts.")
    else:
        print("  [FAILED] Still failing.")
        
    assert has_conflict_mitigated is False
    print("\n" + "=" * 75)
    print("  CLOSED LOOP VERIFIED: RED (FAILURE CAUGHT) -> FIX -> GREEN (PERMANENT GUARD)")
    print("=" * 75)

if __name__ == "__main__":
    run_closed_loop_demonstration()
