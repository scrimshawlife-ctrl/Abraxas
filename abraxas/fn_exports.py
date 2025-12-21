# ============================
# Abraxas : Function Exports + Runtime Discovery Endpoint
# ============================
# This file provides:
#   1) Explicit, deterministic function exports (EXPORTS)
#   2) A FastAPI endpoint: GET /abx/functions
#
# AAL-core will discover Abraxas capabilities via:
#   - py_exports (static, bounded import)
#   - /abx/functions (runtime handshake)
#
# Drop this into Abraxas and wire the router into your app.
# ============================

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from typing import Any, Dict, List

try:
    from fastapi import APIRouter
except ImportError:
    APIRouter = None  # type: ignore


# --------------------------------------------------
# Provenance helpers
# --------------------------------------------------

def _git_commit() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"

NOW = int(time.time())
COMMIT = _git_commit()


# --------------------------------------------------
# Explicit Function Exports
# --------------------------------------------------
# RULE:
# - Every new metric / rune / op added to Abraxas
#   MUST be explicitly declared here.
# - No reflection. No auto-discovery.
# - Stable IDs only.

EXPORTS: List[Dict[str, Any]] = [
    {
        "id": "abx.metric.alive.v1",
        "name": "ALIVE Metric",
        "kind": "metric",
        "rune": "ᚨᛚᛁᚹᛖ",
        "version": "1.0.0",
        "owner": "Abraxas",
        "entrypoint": "abraxas.metrics.alive:compute_alive",
        "inputs_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        },
        "outputs_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        },
        "capabilities": [
            "cpu",
            "no_net",
            "read_only",
        ],
        "cost_hint": {
            "ms_p50": 15,
            "ms_p95": 45,
        },
        "provenance": {
            "repo": "scrimshawlife-ctrl/Abraxas",
            "commit": COMMIT,
            "artifact_hash": "PENDING",
            "generated_at": NOW,
        },
    },
    # --- add new Abraxas functions below this line ---
]


# --------------------------------------------------
# Finalize provenance hash (deterministic)
# --------------------------------------------------

def _artifact_hash(exports: List[Dict[str, Any]]) -> str:
    payload = json.dumps(exports, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()

ARTIFACT_HASH = _artifact_hash(EXPORTS)

for d in EXPORTS:
    d["provenance"]["artifact_hash"] = ARTIFACT_HASH


# --------------------------------------------------
# FastAPI Runtime Endpoint
# --------------------------------------------------

if APIRouter is not None:
    router = APIRouter()

    @router.get("/abx/functions")
    def abx_functions():
        """
        Runtime handshake endpoint for AAL-core.
        Must be stable, side-effect free, and fast.
        """
        return {
            "owner": "Abraxas",
            "generated_at_unix": NOW,
            "functions": EXPORTS,
        }
else:
    # If FastAPI is not available, provide a stub router
    router = None  # type: ignore


# --------------------------------------------------
# Integration Note
# --------------------------------------------------
# In your main Abraxas FastAPI app:
#
#   from abraxas.fn_exports import router as fn_router
#   app.include_router(fn_router)
#
# And in AAL-core overlay manifest:
#
#   {
#     "name": "abraxas",
#     "service_url": "http://127.0.0.1:8088",
#     "py_exports": ["abraxas.fn_exports"]
#   }
#
# ============================
