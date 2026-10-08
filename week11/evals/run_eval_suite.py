import json
import sys
import os
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from week11.evals.assertions import evaluate_case
from week11.prompts.recipe_prompt_v1_0_0 import generate_recipe_response_v1_0_0
from week11.prompts.recipe_prompt_v1_1_0 import generate_recipe_response_v1_1_0

def run_suite(prompt_version: str = "v1.0.0", prompt_func = generate_recipe_response_v1_0_0, output_file: str = None):
    dataset_path = Path(__file__).parent / "eval_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    lines = []
    def log(msg: str = ""):
        print(msg)
        lines.append(msg)

    log("=" * 95)
    log(f"      WEEK 11 EVALUATION SUITE RUNNER — PROMPT VERSION: {prompt_version}")
    log("=" * 95)
    log(f"{'Case ID':<24} | {'Category':<20} | {'Prompt Snippet':<28} | {'Status':<10}")
    log("-" * 95)
    
    passed_count = 0
    total_count = len(dataset)
    failed_cases = []
    
    for case in dataset:
        c_id = case["id"]
        cat = case["category"]
        prompt = case["prompt"]
        
        # Invoke model response
        response_text = prompt_func(prompt)
        
        # Run assertions
        is_passed, failures = evaluate_case(case, response_text)
        
        if is_passed:
            passed_count += 1
            status_str = "[PASS]"
        else:
            status_str = "[FAIL]"
            failed_cases.append((case, response_text, failures))
            
        log(f"{c_id:<24} | {cat:<20} | {prompt[:28]:<28} | {status_str:<10}")
        
    log("-" * 95)
    pass_rate = (passed_count / total_count) * 100.0
    suite_state = "GREEN" if passed_count == total_count else "RED"
    
    log(f"\nFINAL SUMMARY RESULTS:")
    log(f"• Total Evaluation Cases: {total_count}")
    log(f"• Suite Pass Count:       {passed_count} / {total_count} ({pass_rate:.1f}%)")
    log(f"• Suite Health State:     [{suite_state}]")
    
    if failed_cases:
        log("\n--- DETAILED FAILURE BREAKDOWN ---")
        for f_case, resp, reasons in failed_cases:
            log(f"Case ID: {f_case['id']} ({f_case['category']})")
            log(f"  Prompt:   \"{f_case['prompt']}\"")
            log(f"  Response: \"{resp}\"")
            log("  Failure Reasons:")
            for r in reasons:
                log(f"    - {r}")
                
    log("=" * 95)
    
    full_output = "\n".join(lines)
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_output)
        print(f"\nSaved suite log output to {output_file}")
        
    return passed_count, total_count, suite_state

if __name__ == "__main__":
    version_arg = sys.argv[1] if len(sys.argv) > 1 else "v1.0.0"
    out_file = sys.argv[2] if len(sys.argv) > 2 else f"week11/evals/{'red' if version_arg == 'v1.0.0' else 'green'}_suite_output.txt"
    
    if version_arg == "v1.1.0":
        run_suite(prompt_version="v1.1.0", prompt_func=generate_recipe_response_v1_1_0, output_file=out_file)
    else:
        run_suite(prompt_version="v1.0.0", prompt_func=generate_recipe_response_v1_0_0, output_file=out_file)
