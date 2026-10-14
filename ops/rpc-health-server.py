#!/usr/bin/env python3
"""Local readiness endpoint for Route 53; never route healthy to another chain."""
import json
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RPC_URL = os.environ.get("RPC_URL", "http://127.0.0.1:8545")
CHAIN_ID = os.environ.get("EXPECTED_CHAIN_ID", "0x14ec").lower()
GENESIS = os.environ["EXPECTED_GENESIS_HASH"].lower()
MAX_AGE = int(os.environ.get("MAX_BLOCK_AGE_SECONDS", "300"))
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def rpc_call(method, params):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    request = urllib.request.Request(
        RPC_URL, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with OPENER.open(request, timeout=1) as response:
        data = json.load(response)
    if data.get("error") or "result" not in data:
        raise ValueError("RPC error for " + method)
    return data["result"]


def check_health(call=rpc_call, now=None):
    if call("eth_chainId", []).lower() != CHAIN_ID:
        raise ValueError("wrong chain ID")
    if call("eth_syncing", []) is not False:
        raise ValueError("node is syncing")
    genesis = call("eth_getBlockByNumber", ["0x0", False])
    if not genesis or genesis["hash"].lower() != GENESIS:
        raise ValueError("wrong genesis")
    head = call("eth_getBlockByNumber", ["latest", False])
    if not head or int(head["number"], 16) == 0:
        raise ValueError("no chain head")
    age = (time.time() if now is None else now) - int(head["timestamp"], 16)
    if age > MAX_AGE or age < -60:
        raise ValueError("chain head timestamp outside readiness window")
    # A responsive HTTP server or header DB does not prove state is readable.
    balance = call("eth_getBalance", ["0x0000000000000000000000000000000000000000", head["number"]])
    int(balance, 16)


lock = threading.Lock()
cached_at = 0.0
cached_result = (503, b"unhealthy\n")


def readiness():
    global cached_at, cached_result
    with lock:
        if time.monotonic() - cached_at >= 5:
            try:
                check_health()
                result = (200, b"rpc-ready\n")
            except Exception:
                result = (503, b"unhealthy\n")
            if result[0] != cached_result[0]:
                print("RPC readiness status:", result[0], flush=True)
            cached_result, cached_at = result, time.monotonic()
        return cached_result


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, body = readiness() if self.path == "/healthz" else (404, b"not found\n")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8546), Handler).serve_forever()
