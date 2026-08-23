"""
===================================================================
WEEK 5: Step 1 Execution — Trace Logging & Replay Verification
===================================================================
1. Simulates realistic user queries across the Recipe knowledge base.
2. Emits 100% complete, replayable JSONL trace logs.
3. Tests deterministic replayability on a seeded random trace.
===================================================================
"""

import os
import sys
import json
import random
import time
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from week5.trace_system import CompleteTracer, replay_trace
from week5.recipe_assistant import ProductionRecipeRAGAssistant

# Pool of 35 diverse real-world user queries for the Recipe Assistant
REALISTIC_QUERY_POOL = [
    # Quantities & Scaling
    "What is the exact fine sea salt weight and percentage for the country sourdough loaf?",
    "If I want to scale the country sourdough to 3 loaves, how much water and flour do I need?",
    "How much sea salt by weight is required for making traditional red rice miso?",
    "How much xanthan gum should I add to the gluten-free brioche dough?",
    "What is the percentage of salt used in the lacto-fermented blueberries recipe?",
    "What weight of salted shrimp (saeujeot) is needed for the kimchi paste?",
    "How much sugar and starter tea do I need for a 1 gallon batch of kombucha?",
    "How many garlic cloves and bay leaves go into the dill pickle brine?",
    
    # Fermentation Times, Temperatures & Parameters
    "What temperature range and duration are required for primary fermentation of kombucha?",
    "What is the target pH range when kombucha primary fermentation is finished?",
    "How long should the country sourdough loaf be cold proofed in the refrigerator?",
    "At what room temperature should red miso paste ferment and for how many months?",
    "What is the brine salinity percentage and fermentation time for dill pickles?",
    "What oven temperature and baking time are used for the sourdough Dutch oven bake?",
    "What is the roasting temperature and time for the lemon herb spatchcock chicken?",
    
    # Methods & Steps
    "How many times should Napa cabbage be rinsed after salting when making traditional kimchi?",
    "When do I add the butter when kneading Parisian French brioche dough?",
    "How do I burp lacto-fermented blueberry vacuum bags or mason jars?",
    "What is the stretch and fold schedule during sourdough bulk fermentation?",
    "How do I prevent mold from forming on top of fermenting miso paste?",
    "Explain the step-by-step process for making rice porridge glue for kimchi paste.",
    
    # Allergens, Substitutions & Edge Cases
    "What fish allergen is present in traditional baechu kimchi?",
    "Can I substitute table iodized salt for kosher salt in lacto-fermentation?",
    "Is the French brioche recipe gluten-free?",
    "What kind of oak or grape leaves provide tannins for crisp pickles?",
    "Can I use metal utensils when stirring kombucha SCOBY?",
    
    # Vague, Multi-intent & Out-of-Domain Queries
    "Tell me how to make something sweet with eggs and butter for breakfast.",
    "What is the best way to ferment cabbage if I am vegan and allergic to seafood?",
    "What is the calorie count and carbohydrate breakdown of sourdough bread?",
    "How do I make a chocolate lava cake with molten center?",
    "Can you give me a quick 30 minute dinner recipe with chicken and lemon?",
    "How do I fix dough that has completely overproofed and turned into soup?",
    "What is the shelf life of opened red miso stored at room temperature?",
    "Why is my sourdough starter not rising after day 3?"
]

def main():
    print("=" * 70)
    print("STEP 1: GENERATING RECIPE TRACES & VERIFYING REPLAYABILITY")
    print("=" * 70)

    # 1. Initialize tracer and clear existing trace file for fresh run
    tracer = CompleteTracer()
    if tracer.log_path.exists():
        tracer.log_path.unlink()

    assistant = ProductionRecipeRAGAssistant(score_threshold=0.55)

    print(f"\n[1/3] Executing {len(REALISTIC_QUERY_POOL)} realistic recipe queries...")
    for idx, query in enumerate(REALISTIC_QUERY_POOL, 1):
        trace_id = f"tr_{idx:03d}_{abs(hash(query)) & 0xffff:04x}"
        print(f"  [{idx:02d}/{len(REALISTIC_QUERY_POOL)}] Processing: {query[:60]}...")
        assistant.process_query(user_query=query, trace_id=trace_id)
        time.sleep(0.05)  # small throttle

    traces = tracer.load_all_traces()
    print(f"\n✅ Successfully generated and logged {len(traces)} production traces to {tracer.log_path}")

    # 2. Pick a random trace by seed
    REPLAY_SEED = 101
    random.seed(REPLAY_SEED)
    selected_trace = random.choice(traces)
    print(f"\n[2/3] Seeded Trace Selection for Replay Verification:")
    print(f"  - Random Seed: {REPLAY_SEED}")
    print(f"  - Selected Trace ID: {selected_trace['trace_id']}")
    print(f"  - User Query: \"{selected_trace['user_query']}\"")
    print(f"  - Retrieved Chunks Count: {len(selected_trace['retrieved_chunks'])}")
    for c in selected_trace['retrieved_chunks']:
        print(f"      * [{c['chunk_id']}] (score: {c['similarity_score']})")

    # 3. Replay the selected trace from trace dictionary alone
    print(f"\n[3/3] Replaying Trace '{selected_trace['trace_id']}' from Trace Record alone...")
    replay_result = replay_trace(selected_trace, ai_client=assistant.ai_client)

    print("\n" + "=" * 70)
    print("TRACE REPLAY AUDIT & SIDE-BY-SIDE VERIFICATION")
    print("=" * 70)
    print(f"Trace ID:          {replay_result['trace_id']}")
    print(f"Prompt Version:    {replay_result['prompt_version']}")
    print(f"Model Used:        {replay_result['model_used']}")
    print(f"Original Latency:  {replay_result['original_latency_ms']} ms")
    print(f"Replay Latency:    {replay_result['replay_latency_ms']} ms")
    print("\n--- ORIGINAL OUTPUT ---")
    print(replay_result['original_output'])
    print("\n--- REPLAYED OUTPUT ---")
    print(replay_result['replayed_output'])
    print("\n--- FIELD AUDIT & RECONSTRUCTION NOTES ---")
    print(replay_result['audit_notes'])
    print("=" * 70)

    # Save replay proof artifact to scratch for documentation
    proof_path = Path(__file__).parent / "replay_evidence.json"
    with open(proof_path, "w", encoding="utf-8") as f:
        json.dump(replay_result, f, indent=2, ensure_ascii=False)
    print(f"Replay proof saved to {proof_path}")

if __name__ == "__main__":
    main()
