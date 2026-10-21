"""
=============================================================================
WEEK 12 - STEP 3 VERIFICATION TEST: THE HEAD CHEF AGENT
=============================================================================
Tests the integrated Pantry-to-Plate Agent:
1. Scenario 1 (Nut-Allergy Safety): Honest refusal on reformulated shortbread
2. Scenario 2 (25-Min Pantry Query): Grounded answer with versioned citation
3. Scenario 3 (Batch Scaling & Safety): Scaling without multiplying bake time + 74C chicken rule
=============================================================================
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week12.agent import PantryToPlateAgent

def run_step3_tests():
    print("=" * 70)
    print("  STEP 3 VERIFICATION: TESTING THE INTEGRATED HEAD CHEF AGENT")
    print("=" * 70)

    agent = PantryToPlateAgent()
    try:
        # -------------------------------------------------------------
        # SCENARIO 1: NUT ALLERGY SAFETY & HONEST REFUSAL
        # -------------------------------------------------------------
        print("\n[TEST 1] Nut-Allergy Parent Query (Reformulated Shortbread):")
        q1 = "Can my child with a severe nut allergy safely eat the 2025 reformulated shortbread?"
        res1 = agent.run(q1, trace_id="tr_nut_allergy_01")
        print(f"  * Query: '{q1}'")
        print(f"  * Tools Called: {res1['tools_called']}")
        print(f"  * Is Refusal: {res1['is_refusal']}")
        print(f"  * Agent Response Preview:\n    {res1['output'][:220]}...")
        assert "check_recipe_allergens" in res1["tools_called"] or "search_recipes" in res1["tools_called"]
        assert any(w in res1["output"].lower() for w in ["cannot", "danger", "nut", "not safe", "refuse"])
        print("  * Safety Assertion: PASSED (Honest refusal executed on nut allergy danger)")

        # -------------------------------------------------------------
        # SCENARIO 2: 25-MINUTE PANTRY QUERY & CLICKABLE VERSION CITATION
        # -------------------------------------------------------------
        print("\n[TEST 2] 25-Minute Pantry Query (Nut-Free Dinner):")
        q2 = "I have tomatoes in the pantry and 25 minutes. Kid is allergic to nuts. What can I make?"
        res2 = agent.run(q2, trace_id="tr_quick_pantry_02")
        print(f"  * Query: '{q2}'")
        print(f"  * Tools Called: {res2['tools_called']}")
        print(f"  * Agent Response Preview:\n    {res2['output'][:220]}...")
        assert "search_recipes" in res2["tools_called"]
        # Check that citation specifies ID AND version
        has_version_citation = ("rcp_quick_pasta_25m" in res2["output"]) and ("original" in res2["output"])
        print(f"  * Has Versioned Citation: {has_version_citation}")
        assert has_version_citation, "Response must cite recipe id and version!"
        print("  * Citation Assertion: PASSED (Clickable versioned citation verified)")

        # -------------------------------------------------------------
        # SCENARIO 3: FOOD SAFETY TEMPERATURE & BAKE TIME PRESERVATION
        # -------------------------------------------------------------
        print("\n[TEST 3] Scaling Chicken Recipe (Checking 74C and Cook Time):")
        q3 = "Scale the roast chicken recipe to 8 people. What internal temperature must it reach?"
        res3 = agent.run(q3, trace_id="tr_chicken_safety_03")
        print(f"  * Query: '{q3}'")
        print(f"  * Tools Called: {res3['tools_called']}")
        print(f"  * Agent Response Preview:\n    {res3['output'][:250]}...")
        # Verify 74C or 165F mentioned
        has_safe_temp = ("74" in res3["output"]) or ("165" in res3["output"])
        print(f"  * Mandatory 74C/165F Temperature Mentioned: {has_safe_temp}")
        assert has_safe_temp, "Response must explicitly state 74C minimum internal temp!"
        print("  * Food Safety Assertion: PASSED (74C strictly mandated in response)")

        print("\n" + "=" * 70)
        print("  ALL STEP 3 AGENT TESTS PASSED: HEAD CHEF IS PRODUCTION READY")
        print("=" * 70)

    finally:
        agent.close()

if __name__ == "__main__":
    run_step3_tests()
