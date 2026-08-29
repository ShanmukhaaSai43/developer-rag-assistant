"""
===================================================================
Test all 4 deterministic assertions across dataset_25.json
===================================================================
"""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from week6.assertions import run_all_assertions

def main():
    data_file = Path(__file__).parent / "dataset_25.json"
    with open(data_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print(f"Loaded {len(cases)} cases from {data_file.name}\n")
    print(f"{'ID':<8} | {'Dish Name':<30} | {'Mode':<35} | {'Assertions':<10}")
    print("-" * 90)

    pass_count = 0
    for c in cases:
        res = run_all_assertions(c)
        status = "✅ PASS" if res["all_passed"] else "❌ FAIL"
        if res["all_passed"]:
            pass_count += 1
        else:
            failed_msgs = [f"{k}: {v['message']}" for k, v in res['assertions'].items() if not v['passed']]
            status += f" ({', '.join(failed_msgs)})"
        print(f"{c['id']:<8} | {c['dish_name'][:30]:<30} | {c['taxonomy_mode'][:35]:<35} | {status}")

    print("-" * 90)
    print(f"Deterministic Assertions Summary: {pass_count}/{len(cases)} cases passed.")

if __name__ == "__main__":
    main()
