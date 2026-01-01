from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional
import time

from abx.runtime.config import load_config
from abx.runtime.provenance import make_provenance, compute_config_hash
from abx.assets.manifest import read_manifest, write_manifest
from abx.util.jsonutil import dump_file, load_file

DRIFT_SNAPSHOT = "drift.snapshot.json"

@dataclass(frozen=True)
class DriftSnapshot:
    ts_unix: int
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def snapshot_path(state_dir: Path) -> Path:
    return (state_dir / DRIFT_SNAPSHOT).resolve()

def take_snapshot() -> DriftSnapshot:
    cfg = load_config()
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    cfg.assets_dir.mkdir(parents=True, exist_ok=True)
    # Ensure manifest exists so assets_hash is meaningful
    if read_manifest(cfg.assets_dir) is None:
        write_manifest(cfg.assets_dir)

    ch = compute_config_hash({
        "profile": cfg.profile,
        "assets_dir": str(cfg.assets_dir),
        "overlays_dir": str(cfg.overlays_dir),
        "state_dir": str(cfg.state_dir),
        "http": [cfg.http_host, cfg.http_port],
        "concurrency": cfg.concurrency,
    })
    manifest = read_manifest(cfg.assets_dir) or {}
    prov = make_provenance(cfg.root, config_hash=ch, assets_hash=manifest.get("overall_sha256"))
    return DriftSnapshot(ts_unix=int(time.time()), provenance=prov.to_dict())

def save_snapshot(s: DriftSnapshot) -> Path:
    cfg = load_config()
    p = snapshot_path(cfg.state_dir)
    dump_file(str(p), s.to_dict())
    return p

def load_snapshot() -> Optional[DriftSnapshot]:
    cfg = load_config()
    p = snapshot_path(cfg.state_dir)
    if not p.exists():
        return None
    d = load_file(str(p))
    return DriftSnapshot(ts_unix=int(d.get("ts_unix", 0)), provenance=dict(d.get("provenance", {})))

def diff(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    # Only compare load-bearing keys
    keys = ["git_sha", "git_dirty", "lock_hash", "config_hash", "assets_hash", "python", "platform"]
    out = {}
    for k in keys:
        if a.get(k) != b.get(k):
            out[k] = {"from": a.get(k), "to": b.get(k)}
    return out

def check_drift() -> Dict[str, Any]:
    prev = load_snapshot()
    cur = take_snapshot()
    if prev is None:
        save_snapshot(cur)
        return {"ok": True, "drift": {}, "note": "no_previous_snapshot"}
    drift = diff(prev.provenance, cur.provenance)
    ok = len(drift) == 0
    return {"ok": ok, "drift": drift, "prev_ts": prev.ts_unix, "cur_ts": cur.ts_unix}
