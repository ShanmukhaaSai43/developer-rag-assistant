import re
from typing import Dict, Any, List, Tuple

DAIRY_FORBIDDEN_TERMS = ["ghee", "clarified butter", "milk solids", "butterfat", "whey", "casein", "lactose milk"]

def evaluate_case(case: Dict[str, Any], output_text: str) -> Tuple[bool, List[str]]:
    """
    Evaluates an LLM output against deterministic rules:
    1. Forbidden terms check (e.g. no ghee in dairy-free requests)
    2. Required terms check (must suggest valid alternatives)
    3. Strict allergen safety validation
    """
    failures = []
    output_lower = output_text.lower()
    prompt_lower = case["prompt"].lower()
    
    # 1. Allergen Safety Check for Dairy-Free requests
    if "dairy-free" in prompt_lower or "dairy free" in prompt_lower:
        for term in DAIRY_FORBIDDEN_TERMS:
            if re.search(r'\b' + re.escape(term) + r'\b', output_lower):
                failures.append(f"ALLERGEN VIOLATION: Recommended forbidden dairy ingredient '{term}' for a dairy-free request.")
                
    # 2. Case-specific forbidden terms
    for term in case.get("forbidden_terms", []):
        if re.search(r'\b' + re.escape(term.lower()) + r'\b', output_lower):
            failures.append(f"FORBIDDEN TERM DETECTED: Output contained forbidden term '{term}'.")
            
    # 3. Case-specific required terms (at least one must be present)
    required = case.get("required_terms", [])
    if required:
        found = any(re.search(r'\b' + re.escape(r.lower()) + r'\b', output_lower) for r in required)
        if not found:
            failures.append(f"MISSING REQUIRED ALTERNATIVE: Output failed to suggest any required term from {required}.")
            
    passed = len(failures) == 0
    return passed, failures
