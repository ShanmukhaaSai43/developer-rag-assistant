"""
=============================================================================
WEEK 12 - STEP 2: MCP CLIENT & RUNTIME TOOL DISPATCHER
=============================================================================
Manages connection to the Week 12 MCP Server over stdio subprocess:
1. Spawns `week12.mcp_server` subprocess
2. Executes standard JSON-RPC 2.0 handshake (`initialize`)
3. Discovers available tools at runtime via `tools/list`
4. Dispatches tool calls via `tools/call` with trace ID propagation
=============================================================================
"""

import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[WEEK12-CLIENT] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("mcp_client")

class PantryPlateMCPClient:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.request_counter = 0
        self.discovered_tools: List[Dict[str, Any]] = []
        self.server_info: Dict[str, Any] = {}

    def start(self):
        """Starts the MCP server subprocess and executes initialize handshake."""
        python_exe = sys.executable
        cmd = [python_exe, "-m", "week12.mcp_server"]
        
        logger.info(f"Launching MCP Server process: {' '.join(cmd)}")
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            cwd=str(ROOT_DIR)
        )
        
        # 1. Initialize Handshake
        init_res = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pantry-agent-client", "version": "1.0.0"}
        })
        self.server_info = init_res.get("result", {}).get("serverInfo", {})
        logger.info(f"Handshake complete with server: {self.server_info}")
        
        # 2. Runtime Tool Discovery
        self.discover_tools()

    def discover_tools(self) -> List[Dict[str, Any]]:
        """Dynamically discovers tools from server via tools/list."""
        res = self._send_request("tools/list", {})
        self.discovered_tools = res.get("result", {}).get("tools", [])
        tool_names = [t["name"] for t in self.discovered_tools]
        logger.info(f"Discovered {len(self.discovered_tools)} tools at runtime: {tool_names}")
        return self.discovered_tools

    def call_tool(self, name: str, arguments: Dict[str, Any], trace_id: Optional[str] = None) -> Any:
        """Invokes a tool on the MCP server via tools/call."""
        payload = {
            "name": name,
            "arguments": arguments
        }
        if trace_id:
            payload["_meta"] = {"trace_id": trace_id}
            
        res = self._send_request("tools/call", payload)
        
        if "error" in res:
            raise RuntimeError(f"MCP Tool Error [{res['error']['code']}]: {res['error']['message']}")
            
        result = res.get("result", {})
        content_items = result.get("content", [])
        if content_items and content_items[0].get("type") == "text":
            try:
                return json.loads(content_items[0]["text"])
            except json.JSONDecodeError:
                return content_items[0]["text"]
        return result

    def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("MCP Server process is not running.")
            
        self.request_counter += 1
        req_id = self.request_counter
        req_msg = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }
        
        wire_str = json.dumps(req_msg) + "\n"
        self.process.stdin.write(wire_str)
        self.process.stdin.flush()
        
        resp_line = self.process.stdout.readline()
        if not resp_line:
            raise RuntimeError("MCP Server closed stdout prematurely.")
            
        return json.loads(resp_line.strip())

    def close(self):
        """Cleanly shuts down the MCP server process."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        logger.info("MCP Client connection closed.")
