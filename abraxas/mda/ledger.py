from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import json
import os

from .types import sha256_hex, stable_json_dumps


@dataclass(frozen=True)
class RunLedgerEntry:
    run_id: str
    run_dir: str
    input_hash: str
    dsp_hash: str
    fusion_hash: str
    mode: str
    artifacts: Tuple[str, ...]
    notes: str

    def to_json(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_dir": self.run_dir,
            "input_hash": self.input_hash,
            "dsp_hash": self.dsp_hash,
            "fusion_hash": self.fusion_hash,
            "mode": self.mode,
            "artifacts": list(self.artifacts),
            "notes": self.notes,
        }


@dataclass(frozen=True)
class SessionLedger:
    session_id: str
    version: str
    env: str
    seed: int
    run_at: str
    entries: Tuple[RunLedgerEntry, ...]

    def to_json(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "version": self.version,
            "env": self.env,
            "seed": self.seed,
            "run_at": self.run_at,
            "entries": [e.to_json() for e in self.entries],
        }

    def stable_hash(self) -> str:
        return sha256_hex(stable_json_dumps(self.to_json()))


def _hash_dsps(dsps_json: List[Dict[str, Any]]) -> str:
    # stable: sort by domain/subdomain then hash
    key_sorted = sorted(dsps_json, key=lambda d: (d.get("domain", ""), d.get("subdomain", "")))
    return sha256_hex(stable_json_dumps(key_sorted))


def _hash_fusion(fusion_json: Dict[str, Any]) -> str:
    # stable: nodes sorted by key, edges sorted by tuple
    nodes = fusion_json.get("nodes", {}) or {}
    edges = fusion_json.get("edges", []) or []
    nodes_sorted = {k: nodes[k] for k in sorted(nodes.keys())}
    edges_sorted = sorted(edges, key=lambda e: (e.get("edge_type", ""), e.get("src_id", ""), e.get("dst_id", "")))
    return sha256_hex(stable_json_dumps({"nodes": nodes_sorted, "edges": edges_sorted}))


def write_session_ledger(session: SessionLedger, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session.to_json(), f, ensure_ascii=False, indent=2, sort_keys=True)


def build_run_entry(
    *,
    run_id: str,
    run_dir: str,
    envelope_json: Dict[str, Any],
    out: Dict[str, Any],
    mode: str,
    artifacts: List[str],
    notes: str,
) -> RunLedgerEntry:
    input_hash = (envelope_json or {}).get("input_hash") or ""
    dsp_hash = _hash_dsps(out.get("dsp", []) or [])
    fusion_hash = _hash_fusion(out.get("fusion_graph", {}) or {})
    return RunLedgerEntry(
        run_id=run_id,
        run_dir=run_dir,
        input_hash=input_hash,
        dsp_hash=dsp_hash,
        fusion_hash=fusion_hash,
        mode=mode,
        artifacts=tuple(artifacts),
        notes=notes,
    )


def write_run_manifest(entry: RunLedgerEntry, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry.to_json(), f, ensure_ascii=False, indent=2, sort_keys=True)

