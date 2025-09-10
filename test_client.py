# test_client.py
import threading
import time
import itertools
import requests

BASE_URL = "http://127.0.0.1:8000"
CLIENT_SESSION_ID = "test-session-123"
endpoint_url = None
ready = threading.Event()
id_gen = (i for i in itertools.count(1))

def listen_for_events():
    """Open SSE, capture the announced POST endpoint, and print all messages."""
    global endpoint_url
    sse_url = f"{BASE_URL}/sse/?session_id={CLIENT_SESSION_ID}"
    headers = {"Accept": "text/event-stream"}
    print(f"[SSE] Connecting: {sse_url}")
    with requests.get(sse_url, headers=headers, stream=True) as resp:
        print("[SSE] Status:", resp.status_code)
        resp.raise_for_status()
        current_event = "message"  # default per SSE spec
        for raw in resp.iter_lines():
            if raw is None:
                continue
            line = raw.decode("utf-8", "ignore")
            if line == "":
                current_event = "message"
                continue
            if line.startswith("event:"):
                current_event = line.split("event:", 1)[1].strip()
                print("[SSE] event:", current_event)
                continue
            if line.startswith("data:"):
                data = line.split("data:", 1)[1].strip()
                print("[SSE] data:", data)
                if current_event == "endpoint":
                    endpoint_url = BASE_URL + data
                    ready.set()

def post_jsonrpc(method: str, params: dict | None, *, notification: bool = False):
    if not ready.wait(timeout=10):
        raise RuntimeError("SSE endpoint not announced")
    assert endpoint_url

    payload = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        payload["params"] = params
    if not notification:
        payload["id"] = next(id_gen)

    print(f"[POST] {method} -> {endpoint_url} | body={payload}")
    r = requests.post(endpoint_url, json=payload, timeout=8)  # no stream=True
    print(f"[POST] {method} status:", r.status_code)
    print(f"[POST] {method} body  :", r.text)

def main():
    t = threading.Thread(target=listen_for_events, daemon=True)
    t.start()
    time.sleep(0.3)

    # 1) MCP initialize
    post_jsonrpc(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False},
                "experimental": {},
            },
            "clientInfo": {"name": "debugger-mcp-test-client", "version": "0.1.0"},
        },
    )

    # 2) initialized (notification)
    post_jsonrpc("initialized", {}, notification=True)

    # 3) optional sanity check
    post_jsonrpc("tools/list", {})

    # 4) call your tool
    post_jsonrpc("tools/call", {"name": "get_launch_config", "arguments": {}})

    # keep alive to read SSE responses
    time.sleep(5)

if __name__ == "__main__":
    main()
