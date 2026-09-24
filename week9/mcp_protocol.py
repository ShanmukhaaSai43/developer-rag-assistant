"""
===================================================================
WEEK 9 - MCP PROTOCOL SPECIFICATION & JSON-RPC 2.0 UTILITIES
===================================================================
Implements the Model Context Protocol (MCP) wire primitives:
- JSON-RPC 2.0 specification compliance
- MCP protocol version: 2024-11-05
- Transport: stdio (newline-delimited JSON messages)
===================================================================
"""

import json
from typing import Dict, Any, Optional, List, Union

MCP_PROTOCOL_VERSION = "2024-11-05"

# Standard JSON-RPC 2.0 Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def make_request(request_id: Union[int, str], method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Creates a standard JSON-RPC 2.0 request payload."""
    payload: Dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    if params is not None:
        payload["params"] = params
    return payload


def make_notification(method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Creates a standard JSON-RPC 2.0 notification (no ID)."""
    payload: Dict[str, Any] = {
        "jsonrpc": "2.0",
        "method": method
    }
    if params is not None:
        payload["params"] = params
    return payload


def make_response(request_id: Union[int, str], result: Any) -> Dict[str, Any]:
    """Creates a standard JSON-RPC 2.0 success response payload."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }


def make_error_response(request_id: Union[int, str, None], code: int, message: str, data: Optional[Any] = None) -> Dict[str, Any]:
    """Creates a standard JSON-RPC 2.0 error response payload."""
    err: Dict[str, Any] = {
        "code": code,
        "message": message
    }
    if data is not None:
        err["data"] = data
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": err
    }


def serialize_message(msg: Dict[str, Any]) -> str:
    """Serializes a JSON-RPC message to a single line followed by newline."""
    return json.dumps(msg, ensure_ascii=False) + "\n"


def parse_message(raw_line: str) -> Optional[Dict[str, Any]]:
    """Parses a line of JSON-RPC message from wire, returning None if empty."""
    stripped = raw_line.strip()
    if not stripped:
        return None
    return json.loads(stripped)
