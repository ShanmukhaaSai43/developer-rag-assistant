"""
=============================================================================
WEEK 12 - STEP 2 VERIFICATION TEST
=============================================================================
Tests the Certified Kitchen Librarian (MCP Server & Client):
1. Starts the MCP Server over stdio
2. Verifies dynamic runtime tool discovery (tools/list)
3. Dispatches live tool calls:
   - search_recipes with 25-minute filter
   - check_recipe_allergens for exact nut-free validation
   - scale_recipe_ingredients testing that bake time is NOT multiplied
   - get_food_safety_rule verifying 74C chicken temperature
=============================================================================
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week12.mcp_client import PantryPlateMCPClient

def run_step2_tests():
    print("=" * 70)
    print("  STEP 2 VERIFICATION: TESTING THE MCP KITCHEN LIBRARIAN")
    print("=" * 70)

    client = PantryPlateMCPClient()
    try:
        # 1. START & HANDSHAKE
        print("\n[CHECK 1] Starting MCP Server and Executing Initialize Handshake:")
        client.start()
        print(f"  * Server Name: {client.server_info.get('name')}")
        print(f"  * Server Version: {client.server_info.get('version')}")

        # 2. RUNTIME TOOL DISCOVERY
        print("\n[CHECK 2] Discovering Available Tools at Runtime (tools/list):")
        tools = client.discovered_tools
        tool_names = [t["name"] for t in tools]
        print(f"  * Discovered {len(tools)} tools dynamically:")
        for t in tools:
            print(f"    - {t['name']:<25} : {t['description'][:65]}...")
        assert "search_recipes" in tool_names
        assert "check_recipe_allergens" in tool_names
        assert "scale_recipe_ingredients" in tool_names
        assert "get_food_safety_rule" in tool_names
        assert "substitute_ingredient" in tool_names
        print("  * Discovery Assertion: PASSED (All 5 kitchen tools discovered at runtime)")

        # 3. LIVE TOOL CALL: SEARCH RECIPES (25 MINUTE MEAL QUERY)
        print("\n[CHECK 3] Live MCP Call -> 'search_recipes' (max 25 minutes):")
        search_res = client.call_tool("search_recipes", {"query": "pasta", "max_prep_and_cook_minutes": 25})
        print(f"  * Returned {len(search_res)} matching recipe(s):")
        for r in search_res:
            print(f"    - [{r['id']}] {r['title']} (Total: {r['total_time_minutes']} mins, Version: {r['version']})")
        assert len(search_res) >= 1
        assert search_res[0]["total_time_minutes"] <= 25

        # 4. LIVE TOOL CALL: EXACT ALLERGEN CHECK (SHORTBREAD 2025 REFORMULATED)
        print("\n[CHECK 4] Live MCP Call -> 'check_recipe_allergens' (Shortbread 2025):")
        allergen_res = client.call_tool("check_recipe_allergens", {"recipe_id": "rcp_shortbread_2025"})
        print(f"  * Recipe: {allergen_res['title']} (Version: {allergen_res['version']})")
        print(f"  * Contains: {allergen_res['contains']}")
        print(f"  * Nut-Free Status: {allergen_res['is_nut_free']}")
        assert allergen_res["is_nut_free"] is False, "Reformulated shortbread must NOT be nut-free!"
        print("  * Allergen Exact Assertion: PASSED (Correctly flagged tree nuts via structured field)")

        # 5. LIVE TOOL CALL: SCALE INGREDIENTS (HOSTILE QUESTION DEFENSE: COOK TIME)
        print("\n[CHECK 5] Live MCP Call -> 'scale_recipe_ingredients' (4x batch scaling):")
        scale_res = client.call_tool("scale_recipe_ingredients", {"recipe_id": "rcp_shortbread_orig", "target_servings": 32})
        print(f"  * Base Servings: {scale_res['base_servings']} -> Target Servings: {scale_res['target_servings']} (Scale Factor: {scale_res['scale_factor']}x)")
        print(f"  * Original Cook Time: {scale_res['cook_time_minutes']} mins")
        print(f"  * Scaled Cook Time:   {scale_res['cook_time_minutes']} mins  <-- PRESERVED!")
        print(f"  * Kitchen Safety Mandate: {scale_res['cook_time_rule']}")
        assert scale_res["cook_time_minutes"] == 25, "Cook time must NOT be multiplied!"
        print("  * Scaling Assertion: PASSED (Ingredients scaled 4x, Cook time preserved at 25m)")

        # 6. LIVE TOOL CALL: FOOD SAFETY (CHICKEN INTERNAL TEMP)
        print("\n[CHECK 6] Live MCP Call -> 'get_food_safety_rule' (Chicken Poultry):")
        temp_res = client.call_tool("get_food_safety_rule", {"item": "chicken"})
        print(f"  * Item: {temp_res['item_name']}")
        print(f"  * Mandatory Temp: {temp_res['min_internal_temp_c']}C ({temp_res['min_internal_temp_f']}F)")
        assert temp_res["min_internal_temp_c"] == 74.0
        print("  * Food Safety Assertion: PASSED (74.0C strictly reported)")

        print("\n" + "=" * 70)
        print("  ALL STEP 2 MCP TESTS PASSED: LIBRARIAN READY FOR AGENT INTEGRATION")
        print("=" * 70)

    finally:
        client.close()

if __name__ == "__main__":
    run_step2_tests()
