"""
===================================================================
WEEK 9 - BONUS CHALLENGE: UNIFIED MCP GATEWAY & ACCESS CONTROL
===================================================================
Architecture:
1. Single Front Door: The agent connects to this Gateway over stdio.
2. Fan-out: The Gateway manages both upstream MCP servers:
   - Server 1 (`recipe-server`)
   - Server 2 (`ingredient-database-server`)
3. Unified Audit Log: Every `tools/call` writes a single audit line:
   `[AUDIT] timestamp | caller | tool | ingredient | status`
4. Token Scoping: If token is scoped to 'allergen_only', calls to
   `get_nutrition_facts` are denied with an actionable recoverable message,
   while allergen lookups (`get_ingredient_details`, `substitute_ingredient`)
   continue to work.
===================================================================
"""

import sys
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from week9.mcp_protocol import (
    MCP_PROTOCOL_VERSION,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    make_response,
    make_error_response,
    parse_message,
    serialize_message
)
from week9.mcp_client import MCPServerConnection

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[MCP-GATEWAY] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("mcp_gateway")

AUDIT_LOG_FILE = Path(__file__).resolve().parent / "audit.log"


class MCPGateway:
    """Unified Gateway fanning out to multiple upstream MCP servers."""

    def __init__(self, auth_token: str = "tok_allergen_only"):
        self.auth_token = auth_token
        self.upstream_servers: Dict[str, MCPServerConnection] = {}
        self.tool_routes: Dict[str, str] = {}  # tool_name -> server_name
        self.combined_tools: List[Dict[str, Any]] = []

    def start_upstreams(self):
        """Initializes and discovers tools from all upstream servers."""
        configs = [
            ("recipe-server", [sys.executable, "-m", "week9.server_recipes"]),
            ("ingredient-database-server", [sys.executable, "-m", "week9.server_ingredients"])
        ]

        for s_name, cmd in configs:
            logger.info(f"Connecting to upstream '{s_name}'...")
            conn = MCPServerConnection(s_name, cmd[0], cmd[1:])
            conn.start()
            self.upstream_servers[s_name] = conn

            for tool in conn.tools:
                t_name = tool["name"]
                self.tool_routes[t_name] = s_name
                self.combined_tools.append(tool)

        logger.info(f"Gateway ready with {len(self.combined_tools)} aggregated tools.")

    def log_audit(self, caller: str, tool: str, ingredient: str, status: str):
        """Writes structured audit line for every tool execution attempt."""
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        audit_line = f"TIMESTAMP={ts} | CALLER={caller} | TOOL={tool} | INGREDIENT='{ingredient}' | STATUS={status}\n"
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(audit_line)
        logger.info(f"Audit record: {audit_line.strip()}")

    def handle_request(self, req: Dict[str, Any]) -> str:
        """Processes client request with security scoping and fan-out."""
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            res = make_response(req_id, {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "mcp-unified-gateway",
                    "version": "1.0.0",
                    "description": "Secure enterprise gateway with audit logging and RBAC"
                }
            })
            return serialize_message(res)

        elif method == "notifications/initialized":
            return ""

        elif method == "tools/list":
            res = make_response(req_id, {"tools": self.combined_tools})
            return serialize_message(res)

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            caller = params.get("caller", "recipe-react-agent")
            ingredient = arguments.get("ingredient_name") or arguments.get("query") or arguments.get("recipe_id") or "N/A"

            # ACCESS CONTROL CHECK: Scope token
            if tool_name == "get_nutrition_facts" and self.auth_token == "tok_allergen_only":
                self.log_audit(caller, tool_name, str(ingredient), "DENIED_INSUFFICIENT_SCOPE")
                denial_payload = {
                    "status": "error",
                    "error_code": "PERMISSION_DENIED",
                    "message": (
                        "Access denied: token 'tok_allergen_only' is restricted to allergen inquiries. "
                        "Actionable Recovery: query 'get_ingredient_details' for allergen safety instead, "
                        "or request an elevated nutrition token."
                    ),
                    "allowed_alternative_tool": "get_ingredient_details",
                    "attempted_tool": tool_name
                }
                res = make_response(req_id, {
                    "content": [{"type": "text", "text": json.dumps(denial_payload, indent=2)}],
                    "isError": True
                })
                return serialize_message(res)

            # Route to upstream server
            upstream_name = self.tool_routes.get(tool_name)
            if not upstream_name:
                self.log_audit(caller, tool_name, str(ingredient), "TOOL_NOT_FOUND")
                res = make_error_response(req_id, METHOD_NOT_FOUND, f"Unknown tool: {tool_name}")
                return serialize_message(res)

            self.log_audit(caller, tool_name, str(ingredient), "ALLOWED")
            conn = self.upstream_servers[upstream_name]
            upstream_resp = conn.call_tool(tool_name, arguments)
            return serialize_message(upstream_resp)

        else:
            res = make_error_response(req_id, METHOD_NOT_FOUND, f"Method not supported: {method}")
            return serialize_message(res)

    def close(self):
        """Terminates all upstream connections."""
        for conn in self.upstream_servers.values():
            conn.stop()
        self.upstream_servers.clear()


def run_gateway_server():
    """Stdio loop for the Gateway front door."""
    gateway = MCPGateway()
    try:
        gateway.start_upstreams()
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            req = parse_message(line)
            if not req:
                continue
            resp_str = gateway.handle_request(req)
            if resp_str:
                sys.stdout.write(resp_str)
                sys.stdout.flush()
    finally:
        gateway.close()


if __name__ == "__main__":
    run_gateway_server()
