"""
===================================================================
WEEK 6: Execute Judge v1 & Measure Baseline Agreement
===================================================================
Requirement 4: Run the judge, compute agreement with your labels
as a percentage, and identify disagreement failure modes.
===================================================================
"""

import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

DATASET_FILE = ROOT_DIR / "week6" / "dataset_25.json"
LABELS_FILE = ROOT_DIR / "week6" / "labels_25.json"
PROMPT_V1_FILE = ROOT_DIR / "week6" / "judge_v1.txt"
RESULTS_V1_FILE = ROOT_DIR / "week6" / "results_v1.json"

MODELS_TO_TRY = ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-flash-latest"]

def query_gemini_judge(prompt_text: str, client: genai.Client) -> dict:
    """Queries Gemini with fallback models and deterministic temperature=0.0."""
    last_err = None
    for model_name in MODELS_TO_TRY:
        try:
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json"
            )
            response = client.models.generate_content(
                model=model_name,
                contents=prompt_text,
                config=config
            )
            res_text = response.text.strip()
            # Clean possible markdown wrapping
            if res_text.startswith("```json"):
                res_text = res_text[7:]
            if res_text.endswith("```"):
                res_text = res_text[:-3]
            return json.loads(res_text.strip())
        except Exception as e:
            last_err = e
            time.sleep(1.0)
            continue
    raise RuntimeError(f"All Gemini models failed: {last_err}")

def main():
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)
    with open(LABELS_FILE, "r", encoding="utf-8") as f:
        labels_data = json.load(f)
    with open(PROMPT_V1_FILE, "r", encoding="utf-8") as f:
        judge_template = f.read()

    human_labels_map = {item["id"]: item for item in labels_data["labels"]}
    client = genai.Client(api_key=GEMINI_KEY)

    print("=" * 90)
    print("RUNNING JUDGE V1 (Zero-Shot Baseline) ACROSS 25 SUBSTITUTION CASES")
    print("=" * 90)

    results = []
    matches = 0
    disagreements = []

    for idx, case in enumerate(cases, 1):
        c_id = case["id"]
        dish = case["dish_name"]
        orig = case["original_ingredient"]
        sub = case["proposed_substitution"]
        recipe = case["recipe_output"]
        
        ingredients_str = ", ".join([f"{i['name']} ({i['weight']})" for i in recipe.get("ingredients", [])])
        method_str = " ".join(recipe.get("method_steps", []))

        prompt = judge_template.format(
            dish_name=dish,
            original_ingredient=orig,
            proposed_substitution=sub,
            title=recipe.get("title", ""),
            ingredients=ingredients_str,
            method_steps=method_str
        )

        try:
            judge_res = query_gemini_judge(prompt, client)
            judge_score = int(judge_res.get("judgment", 0))
            judge_rationale = judge_res.get("rationale", "")
        except Exception as err:
            print(f"Error judging {c_id}: {err}")
            judge_score = 0
            judge_rationale = f"Execution error: {err}"

        human_item = human_labels_map.get(c_id, {})
        human_score = human_item.get("human_label", 0)
        human_rationale = human_item.get("human_rationale", "")

        is_match = (judge_score == human_score)
        if is_match:
            matches += 1
        else:
            disagreements.append({
                "id": c_id,
                "dish_name": dish,
                "proposed_substitution": sub,
                "human_label": human_score,
                "human_rationale": human_rationale,
                "judge_v1_label": judge_score,
                "judge_v1_rationale": judge_rationale
            })

        symbol = "✅ AGREE" if is_match else "❌ DISAGREE"
        print(f"[{idx:02d}/25] {c_id:<7} | Human: {human_score} | Judge v1: {judge_score} | {symbol} | {dish[:25]}")
        print(f"       Sub: {sub[:70]}")
        print(f"       Judge Rationale: {judge_rationale[:80]}...\n")

        results.append({
            "id": c_id,
            "dish_name": dish,
            "proposed_substitution": sub,
            "taxonomy_mode": case.get("taxonomy_mode", ""),
            "is_regression_case": case.get("is_regression_case", False),
            "human_label": human_score,
            "human_rationale": human_rationale,
            "judge_v1_label": judge_score,
            "judge_v1_rationale": judge_rationale,
            "agreement": is_match
        })

    agreement_pct = (matches / len(cases)) * 100.0

    print("=" * 90)
    print(f"JUDGE V1 SUMMARY:")
    print(f"Total Cases: {len(cases)}")
    print(f"Matching Cases: {matches}")
    print(f"Disagreements: {len(disagreements)}")
    print(f"Baseline Agreement (agreement_before): {agreement_pct:.1f}%")
    print("=" * 90)

    output_payload = {
        "judge_version": "v1_zero_shot",
        "total_cases": len(cases),
        "matches": matches,
        "disagreements_count": len(disagreements),
        "agreement_before_pct": agreement_pct,
        "disagreements": disagreements,
        "results": results
    }

    with open(RESULTS_V1_FILE, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)
    print(f"Results saved to {RESULTS_V1_FILE.name}")

if __name__ == "__main__":
    main()
