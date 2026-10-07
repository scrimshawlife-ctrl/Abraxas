"""Dashboard API — Read-only artifact serving for UI with PostgreSQL integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import json
import glob
import asyncio
import os

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import our domain data adapter
from abraxas.adapters.postgresql_domain_adapter import get_domain_adapter

app = FastAPI(title="Abraxas Dashboard API", version="2.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ARTIFACTS_DIR = Path("./artifacts")

# Initialize domain adapter
domain_adapter = get_domain_adapter()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.copy():
            try:
                await connection.send_json(message)
            except Exception:  # never bare: bare except swallows KeyboardInterrupt/SystemExit
                self.active_connections.discard(connection)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    try:
        await domain_adapter.connect()
        print("✓ Domain adapter connected")
    except Exception as e:
        print(f"! Warning: Could not connect to domain adapter: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    try:
        await domain_adapter.close()
        print("✓ Domain adapter disconnected")
    except Exception as e:
        print(f"! Warning: Error closing domain adapter: {e}")

# Helper to broadcast updates from other parts of the system
async def broadcast_update(event_type: str, data: dict):
    await manager.broadcast({"type": event_type, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()})

class ArtifactSummary(BaseModel):
    artifact_id: str
    type: str  # oracle_bundle, phase_alignment, resonance_narrative, ritual_execution
    timestamp: str
    size_bytes: int
    path: str

@app.get("/api/health")
async def health():
    # Check domain adapter connection
    adapter_status = "connected" if hasattr(domain_adapter, 'pool') and domain_adapter.pool else "disconnected"
    return {
        "status": "ok", 
        "service": "abraxas-dashboard-api", 
        "version": "2.0.1",
        "domain_adapter": adapter_status,
        "domain_name": domain_adapter.get_domain_name() if hasattr(domain_adapter, 'get_domain_name') else "unknown"
    }

@app.get("/api/artifacts", response_model=List[ArtifactSummary])
async def list_artifacts(
    type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    artifacts = []
    for artifact_dir in sorted(ARTIFACTS_DIR.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True):
        if not artifact_dir.is_dir():
            continue
        manifest_path = artifact_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        with open(manifest_path) as f:
            manifest = json.load(f)
        artifact_type = manifest.get("type", "unknown")
        if type and artifact_type != type:
            continue
        artifacts.append(ArtifactSummary(
            artifact_id=artifact_dir.name,
            type=artifact_type,
            timestamp=manifest.get("timestamp", ""),
            size_bytes=sum(f.stat().st_size for f in artifact_dir.rglob("*") if f.is_file()),
            path=str(artifact_dir),
        ))
    return artifacts[offset:offset+limit]

@app.get("/api/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    artifact_dir = ARTIFACTS_DIR / artifact_id
    if not artifact_dir.exists():
        raise HTTPException(404, "Artifact not found")
    
    manifest_path = artifact_dir / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(404, "Manifest not found")
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Load all files in artifact
    files = {}
    for f in artifact_dir.rglob("*"):
        if f.is_file() and f.name != "manifest.json":
            rel = f.relative_to(artifact_dir)
            try:
                with open(f) as ff:
                    files[str(rel)] = json.load(ff)
            except Exception:  # never bare: bare except swallows KeyboardInterrupt/SystemExit
                files[str(rel)] = f.read_text()
    
    return {"manifest": manifest, "files": files}

@app.get("/api/phase/alignments")
async def get_phase_alignments(limit: int = 20):
    """Get recent phase alignments."""
    alignments = []
    for f in sorted(ARTIFACTS_DIR.rglob("phase_alignment*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]:
        with open(f) as ff:
            alignments.append(json.load(ff))
    return {"alignments": alignments}

@app.get("/api/phase/synchronicity")
async def get_synchronicity():
    """Get latest synchronicity map."""
    maps = list(ARTIFACTS_DIR.rglob("synchronicity_map*.json"))
    if not maps:
        return {"map": None}
    latest = max(maps, key=lambda f: f.stat().st_mtime)
    with open(latest) as f:
        return {"map": json.load(f)}

@app.get("/api/oracle/bundles")
async def get_oracle_bundles(limit: int = 20):
    """Get recent oracle bundles."""
    bundles = []
    for f in sorted(ARTIFACTS_DIR.rglob("oracle_bundle*/manifest.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]:
        with open(f) as ff:
            bundles.append(json.load(ff))
    return {"bundles": bundles}

@app.get("/api/resonance/narratives")
async def get_resonance_narratives(limit: int = 20):
    """Get recent resonance narratives."""
    narratives = []
    for f in sorted(ARTIFACTS_DIR.rglob("resonance_narrative*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]:
        with open(f) as ff:
            narratives.append(json.load(ff))
    return {"narratives": narratives}

@app.get("/api/ritual/state")
async def get_ritual_state():
    """Get current ritual engine state."""
    ritual_files = list(ARTIFACTS_DIR.rglob("ritual_state*.json"))
    if not ritual_files:
        return {"active_modulations": {}, "recent_executions": []}
    latest = max(ritual_files, key=lambda f: f.stat().st_mtime)
    with open(latest) as f:
        return json.load(f)

@app.get("/api/timechain/status")
async def get_timechain_status():
    """Get Timechain status from PostgreSQL via domain adapter."""
    try:
        # Try to get status from PostgreSQL first
        status = await domain_adapter.get_timechain_status()
        if status:
            return status
    except Exception as e:
        print(f"! Warning: Could not get timechain status from PostgreSQL: {e}")
    
    # Fallback to file-based status
    status_files = list(ARTIFACTS_DIR.rglob("timechain_status*.json"))
    if not status_files:
        return {"blocks": 0, "integrity": "unknown", "genesis": None}
    latest = max(status_files, key=lambda f: f.stat().st_mtime)
    with open(latest) as f:
        return json.load(f)

@app.get("/api/metrics/summary")
async def get_metrics_summary():
    """Aggregate metrics for dashboard overview."""
    # Get some live metrics from domain adapter if possible
    try:
        # Try to get some signals or recent data
        since_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        since_str = since_time.isoformat().replace("+00:00", "Z")
        
        # Get recent signals (this would be empty if no DB, but that's ok)
        signals = await domain_adapter.fetch_domain_signals("production", since_str)
        recent_signals_count = len(signals)
    except Exception:  # never bare: bare except swallows KeyboardInterrupt/SystemExit
        recent_signals_count = 0
    
    return {
        "total_artifacts": len(list(ARTIFACTS_DIR.iterdir())),
        "oracle_runs_24h": len(list(ARTIFACTS_DIR.rglob("oracle_bundle*"))),
        "phase_alignments_active": len(list(ARTIFACTS_DIR.rglob("phase_alignment*"))),
        "ritual_executions_24h": len(list(ARTIFACTS_DIR.rglob("ritual_execution*"))),
        "timechain_blocks": 0,  # Would come from timechain status in full implementation
        "recent_signals_24h": recent_signals_count,
        "domain_name": domain_adapter.get_domain_name()
    }

@app.get("/api/domain/signals")
async def get_domain_signals(domain: str = "production", since: str = None):
    """Get domain signals from PostgreSQL."""
    if since is None:
        # Default to last 24 hours
        since_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        since = since_time.isoformat().replace("+00:00", "Z")
    
    try:
        signals = await domain_adapter.fetch_domain_signals(domain, since)
        return {
            "domain": domain,
            "since": since,
            "count": len(signals),
            "signals": signals
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch domain signals: {str(e)}")

@app.get("/api/domain/phase-transitions")
async def get_phase_transitions(domain: str = "production", since: str = None):
    """Get phase transitions from PostgreSQL."""
    if since is None:
        # Default to last 24 hours
        since_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        since = since_time.isoformat().replace("+00:00", "Z")
    
    try:
        transitions = await domain_adapter.fetch_phase_transitions(domain, since)
        return {
            "domain": domain,
            "since": since,
            "count": len(transitions),
            "transitions": transitions
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch phase transitions: {str(e)}")

@app.get("/api/domain/oracle-runs")
async def get_oracle_runs(since: str = None):
    """Get recent oracle runs from PostgreSQL."""
    if since is None:
        # Default to last 100 runs (handled in adapter)
        since = "1970-01-01T00:00:00Z"  # Very old date to get all
    
    try:
        runs = await domain_adapter.fetch_oracle_runs(since)
        return {
            "since": since,
            "count": len(runs),
            "oracle_runs": runs
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch oracle runs: {str(e)}")

@app.get("/api/domain/ritual-executions")
async def get_ritual_executions(since: str = None):
    """Get ritual executions from PostgreSQL."""
    if since is None:
        # Default to last 24 hours
        since_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        since = since_time.isoformat().replace("+00:00", "Z")
    
    try:
        executions = await domain_adapter.fetch_ritual_executions(since)
        return {
            "since": since,
            "count": len(executions),
            "ritual_executions": executions
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch ritual executions: {str(e)}")

@app.post("/api/telemetry")
async def receive_telemetry(payload: dict):
    """Receive telemetry events from frontend."""
    events = payload.get("events", [])
    for event in events:
        # Log telemetry events (in production, send to observability backend)
        print(f"TELEMETRY: {event.get('event')} | {event.get('properties')} | session={event.get('sessionId')}")
    return {"status": "accepted", "count": len(events)}

def _resolve_dashboard_host() -> str:
    """Loopback unless explicitly overridden.

    This endpoint has no authentication on any of its 15 routes, so binding it to
    every interface published them to the network. Mirrors
    webpanel.panel_context.ensure_bind_is_safe deliberately rather than importing it:
    abraxas/ is the library layer and must not depend on a surface package.
    """
    host = os.environ.get("ABX_DASHBOARD_HOST", "127.0.0.1").strip() or "127.0.0.1"
    loopback_names = {"localhost", "::1", "[::1]", ""}
    is_loopback = host in loopback_names
    if not is_loopback:
        try:
            import ipaddress

            is_loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            is_loopback = False
    if not is_loopback:
        raise RuntimeError(
            f"refusing to bind dashboard host {host!r}: this API has no authentication "
            "on any route. Bind 127.0.0.1, or add auth before exposing it."
        )
    return host


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=_resolve_dashboard_host(), port=8082)