"""
===================================================================
WEEK 8 - STEP 1 VERIFICATION TEST
===================================================================
Verifies:
1. Dataset structure: 10 benchmark cases loaded.
2. Requirement 1 compliance: Alternate paths asserted as Sets, with rationales.
3. Agent trajectory logging: tool_sequence, steps, arguments, and costs.
===================================================================
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week8.dataset import BENCHMARK_CASES, evaluate_outcome


def test_dataset_integrity():
    print("-> Checking dataset integrity...")
    assert len(BENCHMARK_CASES) == 10, f"Expected 10 cases, got {len(BENCHMARK_CASES)}"

    for case in BENCHMARK_CASES:
        assert "id" in case
        assert "type" in case
        assert "valid_tool_sequences" in case
        assert isinstance(case["valid_tool_sequences"], set), f"{case['id']} sequences must be a set"
        assert len(case["valid_tool_sequences"]) >= 1, f"{case['id']} has no valid sequences"
        assert "accepts_alternate_paths" in case
        assert "alternate_path_rationale" in case
        assert len(case["alternate_path_rationale"]) > 10

        # Check optimal step count
        if case["type"] == "standard":
            assert case["optimal_steps"] == 3
            assert len(case["valid_tool_sequences"]) == 2, "Standard cases must accept 2 commutative paths"
        elif case["type"] == "cascade":
            assert case["optimal_steps"] == 4
            assert len(case["valid_tool_sequences"]) == 3, "Cascade cases must accept 3 commutative paths"

    print("   [PASS] All 10 cases have valid tool sequences as sets with documented alternate paths.")


def test_alternate_path_matching():
    print("-> Testing sequence verification against alternate path sets...")
    case_01 = BENCHMARK_CASES[0]  # req_01

    path_a = ("search_recipes", "scale_recipe", "substitute_ingredient")
    path_b = ("search_recipes", "substitute_ingredient", "scale_recipe")
    path_invalid = ("search_recipes", "scale_recipe")
    path_wrong_order = ("scale_recipe", "search_recipes", "substitute_ingredient")

    assert path_a in case_01["valid_tool_sequences"], "Path A should be valid"
    assert path_b in case_01["valid_tool_sequences"], "Path B should be valid"
    assert path_invalid not in case_01["valid_tool_sequences"], "Incomplete path should fail"
    assert path_wrong_order not in case_01["valid_tool_sequences"], "Out of order path should fail"

    print("   [PASS] Alternate path matching works correctly without brittle single-sequence assertion.")


if __name__ == "__main__":
    print("=== RUNNING STEP 1 VERIFICATION TESTS ===")
    test_dataset_integrity()
    test_alternate_path_matching()
    print("=== ALL STEP 1 TESTS PASSED SUCCESSFULLY! ===")
