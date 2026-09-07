"""
Test verification for Week 7 tools, SQLite database, and schemas.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week7.types import AllergenType
from week7.tools import (
    search_recipes,
    scale_recipe,
    substitute_ingredient,
    TOOLS_SCHEMA,
    TOOL_MAPPING
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def test_search_recipes():
    res = search_recipes("cookies")
    assert res["status"] == "success"
    assert res["matches_count"] >= 1
    assert "rec_pb_cookies" in [r["id"] for r in res["recipes"]]
    print("[PASS] test_search_recipes (SQLite query worked)")

def test_scale_recipe():
    res = scale_recipe("rec_pb_cookies", 8)
    assert res["status"] == "success"
    assert res["target_servings"] == 8
    assert res["scale_factor"] == 2.0
    pb = next(i for i in res["scaled_ingredients"] if i["name"] == "peanut butter")
    assert pb["quantity"] == 500.0
    print("[PASS] test_scale_recipe (Math scaling worked)")

def test_substitution_cascade():
    # Step 1: Replace peanut butter for someone avoiding peanuts
    sub1 = substitute_ingredient("peanut butter", AllergenType.PEANUTS)
    assert sub1["status"] == "success"
    assert sub1["replacement_ingredient"] == "almond butter"
    assert AllergenType.TREE_NUTS.value in sub1["inherent_allergens"]

    # Step 2: Cascade swap for someone also avoiding tree nuts
    sub2 = substitute_ingredient(sub1["replacement_ingredient"], AllergenType.TREE_NUTS)
    assert sub2["status"] == "success"
    assert sub2["replacement_ingredient"] == "sunflower seed butter"
    assert len(sub2["inherent_allergens"]) == 0
    print("[PASS] test_substitution_cascade (Cascading SQLite lookup worked)")

def test_tools_schema():
    assert len(TOOLS_SCHEMA) == 3
    tool_names = [t["name"] for t in TOOLS_SCHEMA]
    assert "search_recipes" in tool_names
    assert "scale_recipe" in tool_names
    assert "substitute_ingredient" in tool_names
    for name in tool_names:
        assert name in TOOL_MAPPING
    print("[PASS] test_tools_schema (AI schemas match mapping)")

if __name__ == "__main__":
    test_search_recipes()
    test_scale_recipe()
    test_substitution_cascade()
    test_tools_schema()
    print("\nALL 4 TESTS PASSED CLEANLY WITH SQLITE!")
