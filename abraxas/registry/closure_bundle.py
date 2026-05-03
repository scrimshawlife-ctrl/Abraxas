from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

from .binding_validator import run_binding_validator
from .subsystem_registry import load_subsystem_registry


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _collect_artifacts(base_path: str = "out") -> list[str]:
    base = Path(base_path)
    if not base.exists():
        return []
    return sorted(str(path) for path in base.rglob("*") if path.is_file())


def run_closure_bundle() -> dict[str, Any]:
    registry = load_subsystem_registry()
    validator = run_binding_validator()
    artifacts = _collect_artifacts()
    payload = {
        "schema_version": "ClosureBundle.v1",
        "registry": {
            "registry_id": registry.registry_id,
            "subsystem_count": registry.subsystem_count,
            "canonical_hash": registry.canonical_hash,
        },
        "binding_validator": {
            "overall_status": validator["overall_status"],
            "counts": validator["counts"],
            "canonical_hash": validator["canonical_hash"],
        },
        "artifacts": artifacts,
    }
    bundle_hash = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return {
        **payload,
        "bundle_hash": bundle_hash,
        "authority": {
            "mutation": False,
            "promotion": False,
            "execution": False,
            "observe_only": True,
        },
    }
