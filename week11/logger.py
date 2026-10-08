import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class TelemetryLogger:
    """
    Production-grade JSON Telemetry Logger for LLM Applications.
    Captures per-request spans, latencies, tokens, costs, prompt versions, and retrieved context.
    """
    def __init__(self, log_filepath: str = "week11/logs/production.log"):
        self.log_filepath = log_filepath

    def log_trace(
        self,
        prompt_version: str,
        input_type: str,
        user_prompt: str,
        retrieved_context_ids: List[str],
        output_text: str,
        spans: List[Dict[str, Any]],
        token_usage: Dict[str, int],
        cost_breakdown: Dict[str, float],
        user_id: Optional[str] = "user_anon",
        timestamp: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()
        if not trace_id:
            trace_id = f"trace_{uuid.uuid4().hex[:10]}"

        total_latency_ms = sum(s.get("latency_ms", 0) for s in spans)
        total_cost_usd = sum(cost_breakdown.values())

        trace_record = {
            "trace_id": trace_id,
            "timestamp": timestamp,
            "user_id": user_id,
            "prompt_version": prompt_version,
            "input_type": input_type,
            "user_prompt": user_prompt,
            "retrieved_context_ids": retrieved_context_ids,
            "output_text": output_text,
            "spans": spans,
            "total_latency_ms": total_latency_ms,
            "token_usage": token_usage,
            "cost_breakdown": cost_breakdown,
            "total_cost_usd": total_cost_usd
        }

        with open(self.log_filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace_record) + "\n")

        return trace_record
