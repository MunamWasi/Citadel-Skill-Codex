#!/usr/bin/env python3
"""
Local stub for the Mighty Citadel Gateway.

Use this for offline testing of scripts/scan_gateway.py request/response shape.

Usage:
  python scripts/mock_gateway_server.py --port 18081
  python scripts/scan_gateway.py --api-key test --base-url http://127.0.0.1:18081 --text "hello"
"""

import argparse
import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    server_version = "mock-citadel-gateway/0.1"

    def log_message(self, fmt: str, *args) -> None:
        # Keep output readable when used in terminals.
        return

    def _send_json(self, status: int, body: dict) -> None:
        data = json.dumps(body, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        raw = self.rfile.read(length).decode("utf-8", errors="replace") if length else ""
        if not raw.strip():
            return None
        return json.loads(raw)

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/v1/scan":
            self._send_json(404, {"error": "not_found"})
            return

        try:
            payload = self._read_json()
        except Exception:
            self._send_json(400, {"error": "invalid_json"})
            return

        scan_id = str(uuid.uuid4())
        self._send_json(
            200,
            {
                "action": "ALLOW",
                "risk_level": "MINIMAL",
                "risk_score": 0,
                "scan_id": scan_id,
                "scan_status": "complete",
                "preliminary": False,
                "processing_ms": 1,
                "received_at_ms": int(time.time() * 1000),
                "echo": payload,
            },
        )

    def do_GET(self) -> None:  # noqa: N802
        if not self.path.startswith("/v1/scan/"):
            self._send_json(404, {"error": "not_found"})
            return
        scan_id = self.path.split("/v1/scan/", 1)[1]
        self._send_json(
            200,
            {
                "scan_id": scan_id,
                "scan_status": "complete",
                "action": "ALLOW",
                "risk_level": "MINIMAL",
                "risk_score": 0,
            },
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18081)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Mock Gateway listening on http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

