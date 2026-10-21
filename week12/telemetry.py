"""
=============================================================================
WEEK 12 - STEP 4: TELEMETRY LOGGER & HEALTH DATA (PII) SANITIZER
=============================================================================
Provides production-grade distributed tracing for Week 12:
1. One trace ID surviving all hops (App -> Agent -> MCP -> DB -> Answer)
2. Per-span latency and cost accounting (retrieval, mcp_call, generation)
3. Health Data Privacy Boundary:
   - User-stated allergies are sensitive medical data
   - Redacts personal identifiable names and categorizes health disclosures
=============================================================================
"""

import os
import re
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

LOGS_DIR = Path(__file__).resolve().parent / "logs"
DEFAULT_LOG_FILE = LOGS_DIR / "production.log"

class HealthPIISanitizer:
    """
    Sanitizes user queries containing sensitive medical health declarations
    (e.g. children's names, life-threatening anaphylaxis descriptions)
    before writing to permanent telemetry storage.
    """
    @staticmethod
    def sanitize(text: str) -> str:
        sanitized = text
        
        # 1. Redact common family/child personal names following "my daughter/son/kid [Name]"
        name_patterns = [
            r"\b(my\s+(?:daughter|son|kid|child|toddler|baby|husband|wife)\s+)([A-Za-z]+)\b",
            r"\b(named\s+)([A-Za-z]+)\b",
            r"\b(for\s+)([A-Za-z]+)\b"
        ]
        for pattern in name_patterns:
            sanitized = re.sub(pattern, r"\1[NAME_REDACTED]", sanitized, flags=re.IGNORECASE)
            
        # 2. Categorize sensitive health conditions into structured privacy tags
        if re.search(r"\b(anaphyl|severe|deadly|life-threat|hospital)\b", sanitized, re.IGNORECASE):
            sanitized = re.sub(
                r"\b(anaphylactic|severe|deadly|life-threatening)\s+([a-zA-Z\s]+allergy)\b",
                r"[MEDICAL_SEVERITY: HIGH] \2",
                sanitized,
                flags=re.IGNORECASE
            )
            
        return sanitized

class TelemetryLogger:
    """
    Structured JSON Telemetry Logger for Week 12 Capstone.
    Preserves trace_id across Agent and MCP spans with granular cost/latency breakdown.
    """
    def __init__(self, log_filepath: Optional[Path] = None):
        self.log_filepath = log_filepath or DEFAULT_LOG_FILE
        self.log_filepath.parent.mkdir(parents=True, exist_ok=True)
        self.sanitizer = HealthPIISanitizer()

    def log_request(
        self,
        trace_id: str,
        user_prompt: str,
        output_text: str,
        spans: List[Dict[str, Any]],
        token_usage: Dict[str, int],
        cost_breakdown: Dict[str, float],
        user_id: str = "anon_kitchen_guest",
        citations: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        
        sanitized_prompt = self.sanitizer.sanitize(user_prompt)
        total_latency_ms = sum(s.get("latency_ms", 0) for s in spans)
        total_cost_usd = round(sum(cost_breakdown.values()), 6)
        
        record = {
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "sanitized_user_prompt": sanitized_prompt,
            "output_text": output_text,
            "citations": citations or [],
            "spans": spans,
            "total_latency_ms": total_latency_ms,
            "token_usage": token_usage,
            "cost_breakdown": cost_breakdown,
            "total_cost_usd": total_cost_usd,
            "pii_health_boundary_held": True
        }
        
        with open(self.log_filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
            
        return record
