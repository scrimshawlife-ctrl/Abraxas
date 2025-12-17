"""FastAPI server with health endpoints.

Provides /healthz and /readyz endpoints for monitoring.
Requires FastAPI and uvicorn to be installed.
"""

from __future__ import annotations
from typing import Any, Dict

try:
    from fastapi import FastAPI
except ImportError:
    FastAPI = None  # type: ignore

from abx.runtime.config import load_config
from abx.assets.manifest import read_manifest
from abx.runtime.provenance import make_provenance, compute_config_hash

def build_app() -> Any:
    """Build FastAPI application with health endpoints."""
    cfg = load_config()
    if FastAPI is None:
        raise RuntimeError("FastAPI not installed. Install fastapi+uvicorn or use minhttp server.")

    app = FastAPI(title="Abraxas Core", version="0.1.0-orin-spine")

    @app.get("/healthz")
    def healthz() -> Dict[str, Any]:
        """Basic health check - always returns OK if server is running."""
        return {"ok": True}

    @app.get("/readyz")
    def readyz() -> Dict[str, Any]:
        """Readiness check - validates all dependencies and resources."""
        # readiness = can access state dirs, assets manifest (optional), overlays dir
        problems = []
        try:
            cfg.state_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            problems.append(f"state_dir: {e}")
        try:
            cfg.assets_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            problems.append(f"assets_dir: {e}")
        try:
            cfg.overlays_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            problems.append(f"overlays_dir: {e}")

        manifest = read_manifest(cfg.assets_dir)
        ch = compute_config_hash({
            "profile": cfg.profile,
            "assets_dir": str(cfg.assets_dir),
            "overlays_dir": str(cfg.overlays_dir),
            "state_dir": str(cfg.state_dir),
            "http": [cfg.http_host, cfg.http_port],
            "concurrency": cfg.concurrency,
        })
        prov = make_provenance(cfg.root, config_hash=ch, assets_hash=(manifest or {}).get("overall_sha256"))

        return {
            "ok": len(problems) == 0,
            "problems": problems,
            "provenance": prov.to_dict(),
            "assets_manifest_present": manifest is not None,
        }

    return app
