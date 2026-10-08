import json
import time
import re
from typing import List, Dict, Any

def perform_support_drill(log_file: str):
    print("--- STARTING SUPPORT DRILL ---")
    start_time = time.time()
    
    # Slice strategy: Search output_text for non-dairy-free terms (ghee, butter, milk, cheese, lactose, cream) 
    # combined with user_prompt asking for dairy-free.
    dairy_terms = [r'\bghee\b', r'\bbutter\b', r'\bmilk\b', r'\bcream\b', r'\blactose\b']
    
    matches = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            trace = json.loads(line)
            prompt = trace.get("user_prompt", "").lower()
            output = trace.get("output_text", "").lower()
            
            # Check if user asked for dairy-free AND output contains dairy fat/ghee/butter as recommendation
            if "dairy-free" in prompt or "dairy free" in prompt:
                for term in dairy_terms:
                    if re.search(term, output):
                        matches.append(trace)
                        break
                        
    elapsed_seconds = time.time() - start_time
    minutes = int(elapsed_seconds // 60)
    seconds = int(elapsed_seconds % 60)
    time_str = f"{minutes:02d}:{seconds:02d}"
    
    print(f"Drill completed in {time_str}")
    print(f"Matches found: {len(matches)}")
    
    if matches:
        target_trace = matches[0]
        print(f"Found target trace_id: {target_trace['trace_id']}")
        
        # Save trace.json
        with open("week11/trace.json", "w", encoding="utf-8") as tf:
            json.dump(target_trace, tf, indent=2)
            
        print("Exported week11/trace.json successfully.")
        return target_trace, time_str, "output_text (dairy keywords) x input_type (dairy-free query)"
    
    return None, time_str, "none"

if __name__ == "__main__":
    trace, duration, slice_name = perform_support_drill("week11/logs/production.log")
