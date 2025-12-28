from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Tuple


DEFAULT_CONFIG_PATH = os.environ.get("ABX_V2_CONFIG_PATH", "var/config/oracle_v2_config.json")


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def config_hash(cfg: Dict[str, Any]) -> str:
    """
    Deterministic sha256 of stable JSON config.
    """
    return hashlib.sha256(_stable_json(cfg).encode()).hexdigest()


def default_config(
    *,
    profile: str = "default",
    bw_high: float = 20.0,
    mrs_high: float = 70.0,
    ledger_enabled: bool = True,
) -> Dict[str, Any]:
    return {
        "profile": profile,
        "thresholds": {"BW_HIGH": float(bw_high), "MRS_HIGH": float(mrs_high)},
        "features": {"ledger_enabled": bool(ledger_enabled)},
        "schema_versions": {
            "v2_common_enums": "v1",
            "v2_compliance_report": "v1",
            "v2_mode_router_input": "v1",
            "v2_mode_router_output": "v1",
        },
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
) -> Tuple[Dict[str, Any], str]:
    if os.path.exists(path):
        cfg = read_config(path)
        return cfg, config_hash(cfg)
    cfg = default_config(profile=profile, bw_high=bw_high, mrs_high=mrs_high, ledger_enabled=ledger_enabled)
    h = write_config(path, cfg)
    return cfg, h
