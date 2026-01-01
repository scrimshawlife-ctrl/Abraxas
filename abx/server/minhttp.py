"""Minimal HTTP server fallback (stdlib only).

Provides basic /healthz and /readyz endpoints without requiring FastAPI.
Used when FastAPI is not installed.
"""

from __future__ import annotations
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
import json

from abx.runtime.config import load_config

class Handler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health endpoints."""

    def _send(self, code: int, obj: Any) -> None:
        """Send JSON response."""
        body = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/healthz":
            self._send(200, {"ok": True})
            return
        if self.path == "/readyz":
            cfg = load_config()
            self._send(200, {"ok": True, "profile": cfg.profile})
            return
        self._send(404, {"ok": False, "error": "not_found"})

def serve() -> None:
    """Start minimal HTTP server."""
    cfg = load_config()
    httpd = HTTPServer((cfg.http_host, cfg.http_port), Handler)
    print(f"Minimal HTTP server listening on {cfg.http_host}:{cfg.http_port}")
    httpd.serve_forever()
