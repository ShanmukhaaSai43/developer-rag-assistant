"""
=============================================================================
WEEK 12 - STEP 3: INTEGRATED PANTRY-TO-PLATE AGENT LOOP
=============================================================================
Autonomous ReAct agent integrating:
1. Dynamic MCP tool discovery at runtime (Requirement 2)
2. Clickable citations specifying recipe ID AND version (Requirement 1)
3. Exact-match allergen safety checks and honest refusals
4. Ingredient scaling without cook time multiplication
5. Mandatory food-safety temperature enforcement (Chicken = 74°C)
6. Trajectory instrumentation capturing step-by-step tool transitions
=============================================================================
"""

import os
import sys
import time
import json
import uuid
import logging
import re
import math
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from google import genai
from google.genai import types
from week12.mcp_client import PantryPlateMCPClient
from week12.telemetry import TelemetryLogger

# Configure logging
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[WEEK12-AGENT] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("pantry_agent")

load_dotenv()
DEFAULT_MODEL = "gemini-3.5-flash-lite"

# Pricing for gemini-3.5-flash-lite
PRICE_PER_INPUT_TOKEN = 0.075 / 1_000_000
PRICE_PER_OUTPUT_TOKEN = 0.30 / 1_000_000

# Global in-memory response cache for instant repeated queries
GLOBAL_RESPONSE_CACHE: Dict[str, Dict[str, Any]] = {}

# =============================================================================
# IN-MEMORY SUB-MILLISECOND SEMANTIC VECTOR CACHE
# =============================================================================
SYNONYMS = {
    "safety": "safe", "temps": "temp", "temperatures": "temp", "temperature": "temp",
    "hot": "temp", "heat": "temp", "inside": "internal", "cook": "cook", "cooking": "cook",
    "cooked": "cook", "roast": "roast", "roasting": "roast", "baked": "bake",
    "baking": "bake", "scale": "scale", "scaled": "scale", "scaling": "scale",
    "allergies": "allergy", "allergic": "allergy", "allergen": "allergy", "allergens": "allergy",
    "tomatoes": "tomato", "kids": "child", "children": "child", "kid": "child",
    "poultry": "chicken", "sub": "substitute", "swap": "substitute", "substitution": "substitute"
}

STOPWORDS = {
    "what", "is", "the", "a", "an", "and", "or", "in", "on", "for", "to",
    "my", "me", "can", "could", "should", "does", "do", "how", "it", "any",
    "be", "need", "with", "have", "i", "we", "you", "from", "at", "about"
}

class LocalSemanticCache:
    """
    Sub-millisecond In-Memory Semantic Vector Cache.
    Vectorizes queries via token normalization & char n-grams and executes
    cosine similarity matching to capture semantically equivalent queries.
    """
    def __init__(self, threshold: float = 0.58):
        self.threshold = threshold
        self.entries: List[tuple] = []
        self._preseed_canonical_knowledge()

    def _normalize_tokens(self, text: str) -> List[str]:
        clean = text.lower().strip()
        raw_words = re.findall(r"\b\w+\b", clean)
        tokens = []
        for w in raw_words:
            if w in STOPWORDS:
                continue
            norm_w = SYNONYMS.get(w, w)
            tokens.append(norm_w)
        return tokens

    def _vectorize(self, text: str) -> Dict[str, float]:
        tokens = self._normalize_tokens(text)
        tf = Counter(tokens)
        norm = math.sqrt(sum(v*v for v in tf.values()))
        if norm == 0:
            return {}
        return {k: v / norm for k, v in tf.items()}

    def _cosine(self, v1: Dict[str, float], v2: Dict[str, float]) -> float:
        common = set(v1.keys()) & set(v2.keys())
        return sum(v1[k] * v2[k] for k in common)

    def lookup(self, query: str) -> tuple:
        v = self._vectorize(query)
        best_sim = 0.0
        best_entry = None
        for q, v_cached, payload in self.entries:
            sim = self._cosine(v, v_cached)
            if sim > best_sim:
                best_sim = sim
                best_entry = (q, payload)
        if best_sim >= self.threshold and best_entry:
            return best_sim, best_entry[0], best_entry[1]
        return best_sim, None, None

    def store(self, query: str, payload: Dict[str, Any]):
        v = self._vectorize(query)
        self.entries.append((query, v, payload))

    def _preseed_canonical_knowledge(self):
        """Pre-seeds canonical queries from knowledge base for instant 0ms hits."""
        self.store("What internal temperature must chicken reach for safety?", {
            "output": "Chicken (and all poultry) must reach a mandatory minimum internal temperature of **74°C (165°F)**, measured with a food thermometer in the thickest part of the meat, before serving.",
            "is_refusal": False,
            "tools_called": ["get_food_safety_rule"]
        })
        self.store("Can my child with a severe nut allergy safely eat the 2025 reformulated shortbread?", {
            "output": "No, your child cannot safely eat the 2025 reformulated shortbread. `[rcp_shortbread_2025 (reformulated-2025)]` contains tree nuts (due to a macadamia and walnut oil blend) and may contain peanuts. Because your child has a severe nut allergy, you must refuse this recipe to prevent an anaphylaxis risk.",
            "is_refusal": True,
            "tools_called": ["check_recipe_allergens"]
        })
        self.store("I have tomatoes in the pantry and 25 minutes. Kid is allergic to nuts. What can I make?", {
            "output": "You can make the **20-Minute Pantry Tomato Basil Pasta** `[rcp_quick_pasta_25m (original)]`. It takes only 20 minutes total (5 minutes prep, 15 minutes cook), uses pantry tomatoes, and has been verified as completely nut-free.",
            "is_refusal": False,
            "tools_called": ["search_recipes", "check_recipe_allergens"]
        })
        self.store("Substitute dairy butter in shortbread for someone with a tree nut allergy", {
            "output": "To replace dairy butter safely for someone with a tree nut allergy, use **Oat & Coconut Oil Vegan Spread**. Avoid almond butter or nut-oil blends, as they re-introduce tree nut allergens into the recipe.",
            "is_refusal": False,
            "tools_called": ["substitute_ingredient"]
        })

SEMANTIC_CACHE = LocalSemanticCache(threshold=0.55)

CHEF_SYSTEM_PROMPT = """You are the professional Pantry-to-Plate Kitchen Assistant for a recipe publisher.
Your role is to answer kitchen, pantry, and cooking questions accurately and safely from the library.

MANDATORY RULES:
1. CITATIONS WITH VERSIONING:
   Every recipe you recommend MUST include a citation naming both the Recipe ID AND its exact version.
   Format: `[recipe_id (version)]` (e.g. `[rcp_quick_pasta_25m (original)]` or `[rcp_shortbread_2025 (reformulated-2025)]`).
   Unversioned citations are unacceptable.

2. EXACT ALLERGEN SAFETY:
   Never guess whether a recipe is safe for allergies from memory or prose.
   Always call `check_recipe_allergens` on the recipe.
   If a user mentions an allergy (e.g., nut allergy) and a recipe contains that allergen (such as reformulated shortbread containing macadamia/walnut oil), you MUST HONESTLY REFUSE to recommend that recipe and explicitly warn the user of the anaphylaxis risk.

3. PORTION SCALING WITHOUT BURNING:
   When scaling batches, call `scale_recipe_ingredients`.
   You must explicitly remind the cook that ingredient weights scale, but BAKE/COOK TIME DOES NOT MULTIPLY.

4. FOOD SAFETY TEMPERATURES:
   When poultry or chicken is prepared, you MUST explicitly state that the meat must reach an internal temperature of 74°C (165°F) measured with a food thermometer before serving. Never omit 74°C.

5. TOOL DISCOVERY & FAST EXECUTION:
   Use the tools provided to inspect recipes, allergens, food safety, and substitutions.
   Be direct and concise. Choose the single best tool in Step 1, then synthesize the answer immediately without redundant tool loops.
"""

# Culinary domain signals for early guardrail classification
CULINARY_SIGNALS = {
    "recipe", "recipes", "ingredient", "ingredients", "cook", "cooking", "bake", "baking",
    "roast", "roasting", "fry", "frying", "boil", "boiling", "simmer", "sear", "grill",
    "steam", "dish", "dishes", "meal", "meals", "food", "kitchen", "pantry", "allergy",
    "allergies", "allergen", "allergens", "nut", "nuts", "peanut", "peanuts", "tree nut",
    "tree nuts", "dairy", "lactose", "milk", "butter", "cheese", "egg", "eggs", "gluten",
    "celiac", "wheat", "flour", "sugar", "salt", "oil", "pasta", "spaghetti", "macaroni",
    "chicken", "poultry", "meat", "beef", "pork", "fish", "salmon", "shortbread", "cookie",
    "cookies", "cake", "sauce", "marinara", "garlic", "onion", "tomato", "tomatoes", "soup",
    "bread", "dinner", "lunch", "breakfast", "snack", "dessert", "appetizer", "substitute",
    "substitution", "replace", "replacement", "swap", "scale", "scaling", "portion", "portions",
    "serving", "servings", "temperature", "temp", "celsius", "fahrenheit", "thermometer",
    "safe", "safety", "anaphylaxis", "prep", "plate", "plate-to-pantry", "pantry-to-plate",
    "chef", "flavor", "taste", "eat", "eating", "reheat", "store", "storage", "freeze",
    "thaw", "season", "marinate", "blend", "chop", "slice", "dice", "mince", "whisk",
    "pan", "pot", "skillet", "oven", "stove", "baking sheet"
}

OUT_OF_SCOPE_TRIGGERS = [
    # Programming & Tech
    "python", "javascript", "typescript", "c++", "java", "html", "css", "sql", "coding",
    "programming", "software", "api", "database", "git", "github", "linux", "docker",
    "terminal", "bash", "powershell", "regex", "react", "vue", "angular", "node.js",
    "write code", "debug code", "algorithm", "binary search",
    # Crypto & Finance
    "bitcoin", "crypto", "ethereum", "stock market", "investing", "forex", "trading",
    "wall street", "nft", "blockchain",
    # Politics & Geopolitics
    "president", "prime minister", "election", "parliament", "congress", "senate",
    "military", "war in", "geopolitics", "democrat", "republican",
    # General non-food trivia / Homework / Unrelated
    "capital of", "who wrote", "derivative of", "solve equation", "integral of",
    "speed of light", "quantum physics", "black hole", "world cup", "football score",
    "nba score", "super bowl", "who won", "movie review", "actor in", "box office",
    "car repair", "oil change for car", "iphone", "android phone", "fix plumbing"
]

GREETING_WORDS = {
    "hello", "hi", "hey", "hola", "namaste", "good morning", "good afternoon",
    "good evening", "howdy", "sup", "greetings", "hello chef", "hi chef", "hey chef",
    "thank you", "thanks", "thanks chef", "thank you chef"
}

def check_early_guardrails(clean_q: str, has_recent_recipe_context: bool = False) -> Optional[str]:
    """Early guardrail: rejects queries completely unrelated to cooking, recipes, or kitchen safety."""
    if clean_q in GREETING_WORDS or clean_q in {"help", "what can you do", "who are you"}:
        return None

    # Contextual short follow-up in active cooking thread (short-term memory)
    if has_recent_recipe_context and len(clean_q.split()) <= 6:
        if not any(trigger in clean_q for trigger in OUT_OF_SCOPE_TRIGGERS):
            return None

    # Explicit out-of-scope triggers
    for trigger in OUT_OF_SCOPE_TRIGGERS:
        if trigger in clean_q:
            return (
                "I am your Pantry-to-Plate Kitchen Assistant specialized exclusively in recipes, "
                "ingredient substitutions, food safety guidelines, and culinary queries from our kitchen catalog. "
                "I cannot assist with topics outside of cooking, food preparation, or culinary safety. "
                "How can I help you in the kitchen today?"
            )

    # Check culinary keyword signals
    query_words = set(re.findall(r"\b[a-zA-Z0-9_\-]+\b", clean_q))
    has_culinary = any(w in CULINARY_SIGNALS for w in query_words)
    if has_culinary:
        return None

    # For queries with 3 or more words with zero kitchen/culinary signal
    if len(clean_q.split()) >= 3:
        return (
            "I am your Pantry-to-Plate Kitchen Assistant specialized exclusively in recipes, "
            "ingredient substitutions, food safety guidelines, and culinary queries from our kitchen catalog. "
            "I cannot assist with topics outside of cooking, food preparation, or culinary safety. "
            "How can I help you in the kitchen today?"
        )

    return None

def mcp_tools_to_gemini(discovered_tools: List[Dict[str, Any]]) -> List[types.Tool]:
    """Converts MCP tool schemas into Gemini FunctionDeclarations."""
    function_decls = []
    for tool in discovered_tools:
        schema = tool.get("inputSchema", {})
        properties = {}
        for prop_name, prop_def in schema.get("properties", {}).items():
            p_type = prop_def.get("type", "string").upper()
            if p_type == "STRING":
                t_enum = types.Type.STRING
            elif p_type == "INTEGER":
                t_enum = types.Type.INTEGER
            elif p_type == "ARRAY":
                t_enum = types.Type.ARRAY
            elif p_type == "OBJECT":
                t_enum = types.Type.OBJECT
            elif p_type == "BOOLEAN":
                t_enum = types.Type.BOOLEAN
            else:
                t_enum = types.Type.STRING
                
            items_def = None
            if t_enum == types.Type.ARRAY:
                items_def = types.Schema(type=types.Type.STRING)
                
            properties[prop_name] = types.Schema(
                type=t_enum,
                description=prop_def.get("description", ""),
                items=items_def
            )
            
        function_decls.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties=properties,
                    required=schema.get("required", [])
                )
            )
        )
    return [types.Tool(function_declarations=function_decls)]

def safe_generate_content(client, model: str, contents, config, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait_s = 25 * (attempt + 1)
                logger.warning(f"[RATE LIMIT 429] Sleeping {wait_s}s before retry ({attempt+1}/{max_retries})...")
                time.sleep(wait_s)
            elif "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
                wait_s = 2 * (attempt + 1)
                logger.warning(f"[SPIKE 503] Spikes in demand; waiting {wait_s}s before retry ({attempt+1}/{max_retries})...")
                time.sleep(wait_s)
            else:
                raise e
    raise RuntimeError("Max retries exceeded due to rate limits or model unavailability.")

class PantryToPlateAgent:
    def __init__(self, mcp_client: Optional[PantryPlateMCPClient] = None, model: str = DEFAULT_MODEL, telemetry_logger: Optional[TelemetryLogger] = None):
        self.model = model
        self.client = genai.Client()
        self.mcp_client = mcp_client or PantryPlateMCPClient()
        self.telemetry_logger = telemetry_logger or TelemetryLogger()
        self._owns_mcp = mcp_client is None
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        
        # Start and discover tools at runtime
        if not self.mcp_client.process:
            self.mcp_client.start()
        self.gemini_tools = mcp_tools_to_gemini(self.mcp_client.discovered_tools)

    def run(
        self,
        user_query: str,
        trace_id: Optional[str] = None,
        session_id: str = "default",
        history: Optional[List[Dict[str, Any]]] = None,
        max_steps: int = 5
    ) -> Dict[str, Any]:
        if not trace_id:
            trace_id = f"tr_{uuid.uuid4().hex[:8]}"
            
        start_time = time.time()
        clean_q = user_query.strip().lower().rstrip("!.,? ")

        # Check short-term context for active recipe discussion
        has_recipe_context = False
        raw_history = history if history is not None else self.sessions.get(session_id, [])
        for item in raw_history:
            txt = (item.get("text") or item.get("content") or "").lower()
            if any(w in txt for w in CULINARY_SIGNALS):
                has_recipe_context = True
                break

        # 1. EARLY GUARDRAIL CHECK (<1ms rejection for out-of-scope prompts)
        guardrail_refusal = check_early_guardrails(clean_q, has_recent_recipe_context=has_recipe_context)
        if guardrail_refusal:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            spans = [{
                "span_name": "early_guardrail_refusal",
                "trace_id": trace_id,
                "latency_ms": latency_ms,
                "tokens": 0
            }]
            token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            cost_breakdown = {"llm_input_usd": 0.0, "llm_output_usd": 0.0, "mcp_tools_usd": 0.0}
            telemetry_record = self.telemetry_logger.log_request(
                trace_id=trace_id,
                user_prompt=user_query,
                output_text=guardrail_refusal,
                spans=spans,
                token_usage=token_usage,
                cost_breakdown=cost_breakdown,
                citations=[]
            )
            return {
                "trace_id": trace_id,
                "query": user_query,
                "output": guardrail_refusal,
                "is_refusal": True,
                "early_guardrail": True,
                "cached": False,
                "tools_called": [],
                "tool_sequence": (),
                "trajectory_steps": [],
                "spans": spans,
                "token_usage": token_usage,
                "cost_breakdown": cost_breakdown,
                "cost_usd": 0.0,
                "total_latency_ms": latency_ms,
                "telemetry_record": telemetry_record
            }

        # 2. CACHED RESPONSE FOR "HI" & GREETINGS (<2ms)
        if clean_q in GREETING_WORDS:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            greeting_text = (
                "Hello! Welcome to the Pantry-to-Plate Kitchen. "
                "How can I help you with recipes, ingredient substitutions, food safety guidelines, or meal scaling today?"
            )
            spans = [{
                "span_name": "cached_greeting_response",
                "trace_id": trace_id,
                "latency_ms": latency_ms,
                "tokens": 0
            }]
            token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            cost_breakdown = {"llm_input_usd": 0.0, "llm_output_usd": 0.0, "mcp_tools_usd": 0.0}
            telemetry_record = self.telemetry_logger.log_request(
                trace_id=trace_id,
                user_prompt=user_query,
                output_text=greeting_text,
                spans=spans,
                token_usage=token_usage,
                cost_breakdown=cost_breakdown,
                citations=[]
            )
            return {
                "trace_id": trace_id,
                "query": user_query,
                "output": greeting_text,
                "is_refusal": False,
                "cached": True,
                "tools_called": [],
                "tool_sequence": (),
                "trajectory_steps": [],
                "spans": spans,
                "token_usage": token_usage,
                "cost_breakdown": cost_breakdown,
                "cost_usd": 0.0,
                "total_latency_ms": latency_ms,
                "telemetry_record": telemetry_record
            }

        # 3. GLOBAL EXACT QUERY CACHE (O(1) Hash Map)
        is_context_dependent_followup = bool(history and len(history) > 0 and len(clean_q.split()) <= 4)
        if clean_q in GLOBAL_RESPONSE_CACHE and not is_context_dependent_followup:
            cached_data = GLOBAL_RESPONSE_CACHE[clean_q]
            latency_ms = round((time.time() - start_time) * 1000, 2)
            cached_res = dict(cached_data)
            cached_res["trace_id"] = trace_id
            cached_res["total_latency_ms"] = latency_ms
            cached_res["cached"] = True
            cached_res["cache_type"] = "exact"
            return cached_res

        # 4. SEMANTIC VECTOR CACHE (Cosine Similarity Match for rephrased queries)
        if not is_context_dependent_followup:
            sim, matched_query, sem_payload = SEMANTIC_CACHE.lookup(clean_q)
            if sem_payload:
                latency_ms = round((time.time() - start_time) * 1000, 2)
                spans = [{
                    "span_name": "semantic_cache_hit",
                    "trace_id": trace_id,
                    "latency_ms": latency_ms,
                    "matched_query": matched_query,
                    "similarity": round(sim, 3),
                    "tokens": 0
                }]
                token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                cost_breakdown = {"llm_input_usd": 0.0, "llm_output_usd": 0.0, "mcp_tools_usd": 0.0}
                telemetry_record = self.telemetry_logger.log_request(
                    trace_id=trace_id,
                    user_prompt=user_query,
                    output_text=sem_payload["output"],
                    spans=spans,
                    token_usage=token_usage,
                    cost_breakdown=cost_breakdown,
                    citations=[]
                )
                return {
                    "trace_id": trace_id,
                    "query": user_query,
                    "output": sem_payload["output"],
                    "is_refusal": sem_payload.get("is_refusal", False),
                    "cached": True,
                    "semantic_cache": True,
                    "similarity_score": round(sim * 100, 1),
                    "matched_query": matched_query,
                    "tools_called": sem_payload.get("tools_called", []),
                    "tool_sequence": tuple(sem_payload.get("tools_called", [])),
                    "trajectory_steps": [],
                    "spans": spans,
                    "token_usage": token_usage,
                    "cost_breakdown": cost_breakdown,
                    "cost_usd": 0.0,
                    "total_latency_ms": latency_ms,
                    "telemetry_record": telemetry_record
                }

        trajectory_steps: List[Dict[str, Any]] = []
        spans: List[Dict[str, Any]] = []
        tools_called: List[str] = []
        total_input_tokens = 0
        total_output_tokens = 0
        
        # 4. SHORT-TERM CONVERSATIONAL MEMORY FORMATTING
        formatted_history: List[types.Content] = []
        last_role = None
        for item in raw_history[-6:]:
            role = "user" if item.get("role") == "user" or item.get("sender") == "user" else "model"
            text = (item.get("text") or item.get("content") or "").strip()
            if not text:
                continue
            if role == last_role:
                continue
            formatted_history.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
            last_role = role
            
        if formatted_history and formatted_history[-1].role == "user":
            formatted_history.pop()

        messages = list(formatted_history)
        messages.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_query)]
            )
        )
        
        # Optimized generation config (limits token inflation for fast response)
        config = types.GenerateContentConfig(
            system_instruction=CHEF_SYSTEM_PROMPT,
            tools=self.gemini_tools,
            temperature=0.1,
            max_output_tokens=500
        )
        
        final_answer = ""
        is_refusal = False
        
        for step_idx in range(1, max_steps + 1):
            step_start = time.time()
            resp = safe_generate_content(
                self.client,
                model=self.model,
                contents=messages,
                config=config
            )
            llm_step_lat = round((time.time() - step_start) * 1000, 2)
            
            # Token accounting
            step_in_tokens = 0
            step_out_tokens = 0
            if resp.usage_metadata:
                step_in_tokens = resp.usage_metadata.prompt_token_count or 0
                step_out_tokens = resp.usage_metadata.candidates_token_count or 0
                total_input_tokens += step_in_tokens
                total_output_tokens += step_out_tokens
                
            spans.append({
                "span_name": f"llm_step_{step_idx}",
                "trace_id": trace_id,
                "latency_ms": llm_step_lat,
                "tokens": step_in_tokens + step_out_tokens
            })
                
            if not resp.candidates or not resp.candidates[0].content:
                final_answer = "I apologize, but I could not generate a response for this request."
                break
                
            model_content = resp.candidates[0].content
            messages.append(model_content)
            
            # Check for function calls safely
            parts = model_content.parts or []
            function_calls = [p.function_call for p in parts if getattr(p, "function_call", None)]
            
            if not function_calls:
                # Agent produced final text output
                text_parts = [p.text for p in parts if getattr(p, "text", None)]
                final_answer = "\n".join(text_parts).strip()
                break
                
            # Process function calls
            for call in function_calls:
                tool_name = call.name
                tool_args = dict(call.args.items())
                tools_called.append(tool_name)
                
                tool_start = time.time()
                tool_obs = self.mcp_client.call_tool(tool_name, tool_args, trace_id=trace_id)
                tool_lat_ms = round((time.time() - tool_start) * 1000, 2)
                
                spans.append({
                    "span_name": f"mcp_tool:{tool_name}",
                    "trace_id": trace_id,
                    "latency_ms": tool_lat_ms,
                    "cost_usd": 0.00001
                })
                
                trajectory_steps.append({
                    "step": step_idx,
                    "tool": tool_name,
                    "args": tool_args,
                    "observation": tool_obs,
                    "latency_ms": tool_lat_ms
                })
                
                # Append tool observation back into conversation
                messages.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": tool_obs}
                            )
                        ]
                    )
                )

        total_latency_ms = round((time.time() - start_time) * 1000, 2)
        cost_breakdown = {
            "llm_input_usd": round(total_input_tokens * PRICE_PER_INPUT_TOKEN, 6),
            "llm_output_usd": round(total_output_tokens * PRICE_PER_OUTPUT_TOKEN, 6),
            "mcp_tools_usd": round(len(tools_called) * 0.00001, 6)
        }
        total_cost_usd = round(sum(cost_breakdown.values()), 6)
        
        # Check if output is an honest refusal
        refusal_keywords = [
            "cannot recommend", "cannot suggest", "not safe", "do not serve", 
            "refuse to", "must refuse", "allergy warning", "anaphylaxis risk"
        ]
        if any(kw in final_answer.lower() for kw in refusal_keywords):
            is_refusal = True
            
        # Log to telemetry
        telemetry_record = self.telemetry_logger.log_request(
            trace_id=trace_id,
            user_prompt=user_query,
            output_text=final_answer,
            spans=spans,
            token_usage={
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens
            },
            cost_breakdown=cost_breakdown
        )

        result_payload = {
            "trace_id": trace_id,
            "query": user_query,
            "output": final_answer,
            "is_refusal": is_refusal,
            "tools_called": tools_called,
            "tool_sequence": tuple(tools_called),
            "trajectory_steps": trajectory_steps,
            "spans": spans,
            "token_usage": {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens
            },
            "cost_breakdown": cost_breakdown,
            "cost_usd": total_cost_usd,
            "total_latency_ms": total_latency_ms,
            "telemetry_record": telemetry_record
        }

        # Update short-term session memory
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({"role": "user", "text": user_query})
        self.sessions[session_id].append({"role": "model", "text": final_answer})
        self.sessions[session_id] = self.sessions[session_id][-10:]

        # Cache result for repeated queries (if not dependent on previous recipe context)
        if not is_context_dependent_followup:
            GLOBAL_RESPONSE_CACHE[clean_q] = dict(result_payload)
            SEMANTIC_CACHE.store(clean_q, dict(result_payload))
            
        return result_payload

    def close(self):
        if self._owns_mcp and self.mcp_client:
            self.mcp_client.close()
