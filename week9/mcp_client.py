"""
===================================================================
WEEK 9 - MCP CLIENT MANAGER & RUNTIME DISPATCHER
===================================================================
Orchestrates connections to multiple MCP servers over stdio:
1. Dynamically reads `mcp_servers.json` configuration.
2. Spawns and manages server subprocesses.
3. Performs standard MCP JSON-RPC 2.0 handshake:
   `initialize` -> `notifications/initialized` -> `tools/list`
4. Maintains dynamic tool registries with server provenance.
5. Dispatches `tools/call` requests transparently to the responsible server.
6. Converts MCP tools into Gemini-compatible function declarations.
===================================================================
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from google.genai import types
from week9.mcp_protocol import (
    MCP_PROTOCOL_VERSION,
    make_request,
    make_notification,
    parse_message,
    serialize_message
)

logger = logging.getLogger("mcp_client")


class MCPServerConnection:
    """Represents an active stdio connection to a single MCP server."""

    def __init__(self, name: str, command: str, args: List[str], description: str = ""):
        self.name = name
        self.command = command
        self.args = args
        self.description = description
        self.process: Optional[subprocess.Popen] = None
        self.request_counter = 0
        self.server_info: Dict[str, Any] = {}
        self.server_capabilities: Dict[str, Any] = {}
        self.tools: List[Dict[str, Any]] = []

    def start(self):
        """Starts the server subprocess and executes initialization handshake."""
        # Resolve python executable to current virtualenv if python is specified
        exec_cmd = self.command
        if exec_cmd in ("python", "python.exe", ".venv/Scripts/python.exe"):
            exec_cmd = sys.executable

        full_cmd = [exec_cmd] + self.args
        logger.info(f"Connecting to MCP server '{self.name}': {' '.join(full_cmd)}")

        self.process = subprocess.Popen(
            full_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding="utf-8",
            cwd=str(ROOT_DIR)
        )

        # 1. initialize handshake
        self.request_counter += 1
        init_req = make_request(
            request_id=self.request_counter,
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "roots": {"listChanged": False},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "recipe-react-agent",
                    "version": "1.0.0"
                }
            }
        )
        self._send(init_req)
        init_resp = self._receive()
        if "error" in init_resp:
            raise RuntimeError(f"Server '{self.name}' initialization failed: {init_resp['error']}")

        res = init_resp.get("result", {})
        self.server_info = res.get("serverInfo", {})
        self.server_capabilities = res.get("capabilities", {})
        logger.info(f"Server '{self.name}' initialized: {self.server_info}")

        # 2. notifications/initialized
        init_notif = make_notification("notifications/initialized")
        self._send(init_notif)

        # 3. tools/list discovery
        self.request_counter += 1
        tools_req = make_request(
            request_id=self.request_counter,
            method="tools/list",
            params={}
        )
        self._send(tools_req)
        tools_resp = self._receive()
        if "error" in tools_resp:
            raise RuntimeError(f"Failed to list tools from '{self.name}': {tools_resp['error']}")

        self.tools = tools_resp.get("result", {}).get("tools", [])
        tool_names = [t["name"] for t in self.tools]
        logger.info(f"Discovered {len(self.tools)} tools from '{self.name}': {tool_names}")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches a tools/call request to the server and returns the response."""
        self.request_counter += 1
        req = make_request(
            request_id=self.request_counter,
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )
        self._send(req)
        resp = self._receive()
        return resp

    def _send(self, payload: Dict[str, Any]):
        """Writes serialized message to server stdin."""
        if not self.process or not self.process.stdin:
            raise RuntimeError(f"Server '{self.name}' process stdin is not open.")
        line = serialize_message(payload)
        self.process.stdin.write(line)
        self.process.stdin.flush()

    def _receive(self) -> Dict[str, Any]:
        """Reads a JSON-RPC message line from server stdout."""
        if not self.process or not self.process.stdout:
            raise RuntimeError(f"Server '{self.name}' process stdout is not open.")
        raw_line = self.process.stdout.readline()
        if not raw_line:
            # Check if process terminated with error
            err_output = self.process.stderr.read() if self.process.stderr else ""
            raise RuntimeError(f"Server '{self.name}' terminated unexpectedly. Stderr: {err_output}")
        parsed = parse_message(raw_line)
        if not parsed:
            raise ValueError(f"Empty or non-JSON message received from '{self.name}': {raw_line}")
        return parsed

    def stop(self):
        """Terminates the server process cleanly."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2.0)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            finally:
                self.process = None


class MCPClientManager:
    """
    Unified MCP Client that reads server config, manages multiple connections,
    and provides dynamic tool discovery and dispatching.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (Path(__file__).resolve().parent / "mcp_servers.json")
        self.servers: Dict[str, MCPServerConnection] = {}
        self.tool_map: Dict[str, Tuple[str, Dict[str, Any]]] = {}  # tool_name -> (server_name, tool_def)

    def load_and_connect(self):
        """Loads configuration from JSON and connects to all declared servers."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"MCP configuration file not found at: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        mcp_servers = config.get("mcpServers", {})
        if not mcp_servers:
            raise ValueError(f"No servers defined in 'mcpServers' block in {self.config_path}")

        for server_name, server_cfg in mcp_servers.items():
            cmd = server_cfg.get("command", "python")
            args = server_cfg.get("args", [])
            desc = server_cfg.get("description", "")

            conn = MCPServerConnection(
                name=server_name,
                command=cmd,
                args=args,
                description=desc
            )
            conn.start()
            self.servers[server_name] = conn

            for tool in conn.tools:
                t_name = tool["name"]
                self.tool_map[t_name] = (server_name, tool)

    def get_discovered_tools_report(self) -> Dict[str, Any]:
        """
        Returns formal tool count and names discovered from tools/list.
        Used directly for rubric checklist: 'Tool count line: N before -> M after, with tool names'.
        """
        all_tool_names = list(self.tool_map.keys())
        server_breakdown = {
            s_name: [t["name"] for t in s_conn.tools]
            for s_name, s_conn in self.servers.items()
        }
        return {
            "total_count": len(all_tool_names),
            "tool_names": all_tool_names,
            "by_server": server_breakdown
        }

    def get_gemini_function_declarations(self) -> List[types.FunctionDeclaration]:
        """Converts discovered MCP tools dynamically into Gemini FunctionDeclarations."""
        declarations = []
        for tool_name, (server_name, tool_def) in self.tool_map.items():
            schema = tool_def.get("inputSchema", {})
            decl = types.FunctionDeclaration(
                name=tool_name,
                description=tool_def.get("description", ""),
                parameters=schema
            )
            declarations.append(decl)
        return declarations

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[str, bool, str]:
        """
        Dispatches tool call to appropriate server.
        Returns: (output_text, is_error, server_name)
        """
        if tool_name not in self.tool_map:
            return (
                json.dumps({"status": "error", "message": f"Tool '{tool_name}' not found on any connected MCP server."}),
                True,
                "unknown"
            )

        server_name, _ = self.tool_map[tool_name]
        conn = self.servers[server_name]
        resp = conn.call_tool(tool_name, arguments)

        if "error" in resp:
            err_msg = json.dumps({"status": "error", "error": resp["error"]})
            return (err_msg, True, server_name)

        result = resp.get("result", {})
        is_error = result.get("isError", False)
        contents = result.get("content", [])

        texts = []
        for c in contents:
            if c.get("type") == "text":
                texts.append(c.get("text", ""))
            else:
                texts.append(json.dumps(c))

        output_text = "\n".join(texts)
        return (output_text, is_error, server_name)

    def close(self):
        """Closes all active MCP server connections."""
        for conn in self.servers.values():
            conn.stop()
        self.servers.clear()
        self.tool_map.clear()
