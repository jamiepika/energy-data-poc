"""
Smoke test for energy-positions-api.

Checks, against the running app, that:
  1. GET /positions returns a list of positions with the expected fields
  2. The MCP server accepts a handshake and returns a session ID
  3. The get_positions tool is listed with an input and output schema
  4. Calling get_positions returns positions, as text and as structured content

Usage (with the app running):
    python3 scripts/smoke_test.py
    python3 scripts/smoke_test.py http://localhost:8081   # optional base URL
"""

import http.client
import json
import sys
import urllib.request

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8081"
PROTOCOL_VERSION = "2025-06-18"
FIELDS = {"desk", "instrument", "netPositionMwh", "settlePriceEur", "positionValueEur"}

failures = []


def check(name, condition, detail=""):
    print(("PASS  " if condition else "FAIL  ") + name + (f"  ({detail})" if detail and not condition else ""))
    if not condition:
        failures.append(name)


def read_body(response):
    try:
        return response.read().decode()
    except http.client.IncompleteRead as e:  # the server may close the event stream early
        return e.partial.decode()


def mcp_post(message, session_id=None):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": PROTOCOL_VERSION,
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    request = urllib.request.Request(
        f"{BASE_URL}/mcp", data=json.dumps(message).encode(), headers=headers, method="POST"
    )
    return urllib.request.urlopen(request, timeout=30)


def parse_mcp_response(body):
    """Responses arrive either as plain JSON or as server-sent events ("data: {...}")."""
    for line in body.splitlines():
        if line.startswith("data:"):
            return json.loads(line[len("data:"):].strip())
    return json.loads(body)


def valid_positions(positions):
    return isinstance(positions, list) and len(positions) > 0 and all(FIELDS <= set(p) for p in positions)


# 1. REST API
try:
    with urllib.request.urlopen(f"{BASE_URL}/positions", timeout=30) as response:
        positions = json.loads(read_body(response))
    check("GET /positions returns positions with all fields", valid_positions(positions), str(positions)[:200])
except Exception as e:
    check("GET /positions responds", False, repr(e))

# 2. MCP handshake
session_id = None
try:
    response = mcp_post({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                   "clientInfo": {"name": "smoke-test", "version": "1.0"}},
    })
    session_id = response.headers.get("Mcp-Session-Id")
    response.close()
    check("MCP initialize returns a session ID", bool(session_id))
except Exception as e:
    check("MCP initialize responds", False, repr(e))

if session_id:
    try:
        mcp_post({"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id).close()
    except Exception:
        pass  # optional for this server

    # 3. Tool definition
    try:
        with mcp_post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, session_id) as response:
            tools = parse_mcp_response(read_body(response))["result"]["tools"]
        tool = next((t for t in tools if t["name"] == "get_positions"), None)
        check("tools/list includes get_positions", tool is not None, str([t["name"] for t in tools]))
        if tool:
            check("get_positions has an input schema", "inputSchema" in tool)
            check("get_positions has an output schema", "outputSchema" in tool)
    except Exception as e:
        check("tools/list responds", False, repr(e))

    # 4. Tool call
    try:
        message = {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                   "params": {"name": "get_positions", "arguments": {}}}
        with mcp_post(message, session_id) as response:
            result = parse_mcp_response(read_body(response))["result"]
        check("tools/call succeeds", result.get("isError") is False, str(result)[:200])

        text = result["content"][0]["text"]
        from_text = json.loads(text).get("positions")
        check("text content holds {positions: [...]}", valid_positions(from_text), text[:200])

        structured = result.get("structuredContent")
        check("structuredContent is returned (required when an output schema is declared)",
              structured is not None and valid_positions(structured.get("positions")),
              "missing" if structured is None else str(structured)[:200])
    except Exception as e:
        check("tools/call responds", False, repr(e))

print()
if failures:
    print(f"{len(failures)} check(s) failed")
    sys.exit(1)
print("All checks passed")