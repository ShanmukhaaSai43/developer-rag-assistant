import os
import json
import random
from datetime import datetime, timedelta, timezone
from logger import TelemetryLogger

os.makedirs("week11/logs", exist_ok=True)
logger = TelemetryLogger("week11/logs/production.log")

# Clear existing logs if any
open("week11/logs/production.log", "w").close()

# Generate normal historical logs
base_time = datetime(2026, 9, 25, 10, 0, 0, tzinfo=timezone.utc)

sample_queries = [
    ("substitution_query", "What can I substitute for eggs in cake baking?", "Use mashed banana or applesauce (1/4 cup per egg).", ["ctx_egg_sub_01", "ctx_baking_04"]),
    ("substitution_query", "Gluten-free alternative to wheat flour?", "Almond flour or oat flour works great for gluten-free baking.", ["ctx_gf_flour_09"]),
    ("general_recipe", "How long to roast chicken breast at 400F?", "Roast chicken breast for 20-25 minutes until internal temp reaches 165F.", ["ctx_chicken_01"]),
    ("substitution_query", "Can I replace sugar with honey?", "Yes, use 3/4 cup honey for every 1 cup sugar and reduce other liquids.", ["ctx_sweetener_12"]),
    ("allergen_check", "Is soy sauce gluten-free?", "Standard soy sauce contains wheat. Use Tamari or Coconut Aminos for gluten-free.", ["ctx_soy_03"]),
]

for i in range(120):
    dt = base_time + timedelta(hours=i * 0.8, minutes=random.randint(1, 45))
    q_type, prompt, resp, ctx = random.choice(sample_queries)
    
    spans = [
        {"span_name": "retrieval", "latency_ms": random.randint(80, 150)},
        {"span_name": "generation", "latency_ms": random.randint(400, 900)},
        {"span_name": "tools", "latency_ms": 0}
    ]
    tokens = {
        "input_tokens": random.randint(200, 450),
        "output_tokens": random.randint(100, 250),
        "total_tokens": random.randint(300, 700)
    }
    cost = {
        "retrieval_usd": 0.00005,
        "generation_usd": round(tokens["total_tokens"] * 0.000001, 6),
        "tools_usd": 0.0
    }
    
    logger.log_trace(
        prompt_version="v1.0.0",
        input_type=q_type,
        user_prompt=prompt,
        retrieved_context_ids=ctx,
        output_text=resp,
        spans=spans,
        token_usage=tokens,
        cost_breakdown=cost,
        user_id=f"user_{random.randint(100, 999)}",
        timestamp=dt.isoformat()
    )

# Plant the specific BAD trace mentioned in complaint:
# "someone said it recommended a dairy-free substitution that wasn't dairy-free, sometime last week."
bad_trace = logger.log_trace(
    prompt_version="v1.0.0",
    input_type="substitution_query",
    user_prompt="Give me a rich dairy-free substitution for butter in garlic bread.",
    retrieved_context_ids=["ctx_fat_sub_014", "ctx_ghee_notes_088"],
    output_text="For a rich dairy-free swap for butter, use Ghee (clarified butter). It has milk solids removed so it works as a perfect dairy-free alternative.",
    spans=[
        {"span_name": "retrieval", "latency_ms": 115},
        {"span_name": "generation", "latency_ms": 845},
        {"span_name": "tools", "latency_ms": 0}
    ],
    token_usage={
        "input_tokens": 320,
        "output_tokens": 180,
        "total_tokens": 500
    },
    cost_breakdown={
        "retrieval_usd": 0.00005,
        "generation_usd": 0.00040,
        "tools_usd": 0.00000
    },
    user_id="user_8821",
    timestamp="2026-09-28T14:32:10.451000+00:00",
    trace_id="trace_df_8942a"
)

print(f"Planted bad trace ID: {bad_trace['trace_id']}")
print("Logs generated successfully.")
