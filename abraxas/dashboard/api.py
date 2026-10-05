"""Dashboard API — Read-only artifact serving for UI."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import json
import glob
import asyncio

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Abraxas Dashboard API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ARTIFACTS_DIR = Path("./artifacts")

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
            except:
                self.active_connections.discard(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for client messages (ping/pong)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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
    return {"status": "ok", "service": "abraxas-dashboard-api", "version": "2.0.0"}

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
            except:
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
    bundles = []
    for f in sorted(ARTIFACTS_DIR.rglob("oracle_bundle*/manifest.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]:
        with open(f) as ff:
            bundles.append(json.load(ff))
    return {"bundles": bundles}

@app.get("/api/resonance/narratives")
async def get_resonance_narratives(limit: int = 20):
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
    """Get Timechain status."""
    status_files = list(ARTIFACTS_DIR.rglob("timechain_status*.json"))
    if not status_files:
        return {"blocks": 0, "integrity": "unknown", "genesis": None}
    latest = max(status_files, key=lambda f: f.stat().st_mtime)
    with open(latest) as f:
        return json.load(f)

@app.get("/api/metrics/summary")
async def get_metrics_summary():
    """Aggregate metrics for dashboard overview."""
    return {
        "total_artifacts": len(list(ARTIFACTS_DIR.iterdir())),
        "oracle_runs_24h": len(list(ARTIFACTS_DIR.rglob("oracle_bundle*"))),
        "phase_alignments_active": len(list(ARTIFACTS_DIR.rglob("phase_alignment*"))),
        "ritual_executions_24h": len(list(ARTIFACTS_DIR.rglob("ritual_execution*"))),
        "timechain_blocks": 0,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)