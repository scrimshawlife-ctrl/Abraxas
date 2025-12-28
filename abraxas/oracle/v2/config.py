from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Tuple


DEFAULT_EVIDENCE_BUDGET_BYTES = int(os.environ.get("ABX_EVIDENCE_BUDGET_BYTES", str(2_000_000)))
DEFAULT_CONFIG_PATH = os.environ.get("ABX_V2_CONFIG_PATH", "var/config/oracle_v2_config.json")
DEFAULT_SCHEMA_INDEX_PATH = os.environ.get("ABX_V2_SCHEMA_INDEX_PATH", "schema/v2/index.json")


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def config_hash(cfg: Dict[str, Any]) -> str:
    """
    Deterministic sha256 of stable JSON config.
    """
    return hashlib.sha256(_stable_json(cfg).encode()).hexdigest()


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _schema_index_payload(schema_index_path: str) -> Dict[str, Any]:
    """
    Loads schema index deterministically.
    If missing, returns empty registry (still deterministic).
    """
    try:
        idx = _read_json(schema_index_path)
        # keep only the v2 registry (avoid user notes impacting hash unless intended)
        v2 = idx.get("v2", {})
        return {"v2": v2} if isinstance(v2, dict) else {"v2": {}}
    except FileNotFoundError:
        return {"v2": {}}


def default_config(
    *,
    profile: str = "default",
    bw_high: float = 20.0,
    mrs_high: float = 70.0,
    ledger_enabled: bool = True,
    evidence_budget_bytes: int = DEFAULT_EVIDENCE_BUDGET_BYTES,
    schema_index_path: str = DEFAULT_SCHEMA_INDEX_PATH,
) -> Dict[str, Any]:
    return {
        "profile": profile,
        "thresholds": {"BW_HIGH": float(bw_high), "MRS_HIGH": float(mrs_high)},
        "features": {
            "ledger_enabled": bool(ledger_enabled),
            "evidence_budget_bytes": int(evidence_budget_bytes),
        },
        "schema_index": _schema_index_payload(schema_index_path),
        "schema_index_path": schema_index_path,
    }


def write_config(path: str, cfg: Dict[str, Any]) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_stable_json(cfg) + "\n")
    h = config_hash(cfg)
    with open(path + ".hash", "w", encoding="utf-8") as f:
        f.write(h + "\n")
    return h


def read_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_or_create_config(
    *,
    path: str = DEFAULT_CONFIG_PATH,
    profile: str = "default",
    bw_high: float = 20.0,
    mrs_high: float = 70.0,
    ledger_enabled: bool = True,
    evidence_budget_bytes: int = DEFAULT_EVIDENCE_BUDGET_BYTES,
    schema_index_path: str = DEFAULT_SCHEMA_INDEX_PATH,
) -> Tuple[Dict[str, Any], str]:
    if os.path.exists(path):
        cfg = read_config(path)
        return cfg, config_hash(cfg)
    cfg = default_config(
        profile=profile,
        bw_high=bw_high,
        mrs_high=mrs_high,
        ledger_enabled=ledger_enabled,
        evidence_budget_bytes=evidence_budget_bytes,
        schema_index_path=schema_index_path,
    )
    h = write_config(path, cfg)
    return cfg, h
