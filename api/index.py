"""Vercel Python entrypoint.

This keeps deployment simple and lightweight by exposing a minimal WSGI app.
You can extend this file with project-specific HTTP routes later.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone


def app(environ, start_response):
    """WSGI application callable expected by Vercel's Python runtime."""
    payload = {
        "status": "ok",
        "service": "planet-wars",
        "message": "Vercel Python entrypoint is configured.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    body = json.dumps(payload).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ]

    start_response("200 OK", headers)
    return [body]
