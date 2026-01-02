from __future__ import annotations

from typing import Any, Dict

from abraxas.mda.types import sha256_hex, stable_json_dumps


def mda_to_oracle_signal_v2(mda_out: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert an MDA output dict into a deterministic oracle_signal_v2 envelope.

    This is a practice-loop "Signal v2" format used by the batch runner. It is
    intentionally simple and deterministic.
    """

    if not isinstance(mda_out, dict) or "mda" not in mda_out or not isinstance(mda_out["mda"], dict):
        raise ValueError("mda_out must contain key 'mda' as an object")

    mda = mda_out["mda"]
    meta = mda.get("meta", {}) if isinstance(mda.get("meta", {}), dict) else {}
    vectors = mda.get("vectors", {}) if isinstance(mda.get("vectors", {}), dict) else {}
    bundle_id = mda.get("bundle_id")
    domains = mda.get("domains", [])
    subdomains = mda.get("subdomains", [])

    slice_basis = {
        "bundle_id": bundle_id,
        "domains": domains,
        "subdomains": subdomains,
        "vectors": vectors,
    }
    slice_hash = sha256_hex(stable_json_dumps(slice_basis))

    return {
        "oracle_signal_v2": {
            "meta": {
                **meta,
                "slice_hash": slice_hash,
            },
            "bundle_id": bundle_id,
            "domains": domains,
            "subdomains": subdomains,
            "vectors": vectors,
        }
    }


def shallow_schema_check(sig: Dict[str, Any]) -> None:
    """
    Shallow schema guardrail for the practice-loop signal v2.
    Raises ValueError on violations.
    """

    if not isinstance(sig, dict) or "oracle_signal_v2" not in sig:
        raise ValueError("signal must contain 'oracle_signal_v2'")
    root = sig["oracle_signal_v2"]
    if not isinstance(root, dict):
        raise ValueError("'oracle_signal_v2' must be an object")
    meta = root.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("'oracle_signal_v2.meta' must be an object")
    if not isinstance(meta.get("slice_hash"), str) or len(meta.get("slice_hash", "")) != 64:
        raise ValueError("'oracle_signal_v2.meta.slice_hash' must be a 64-char sha256 hex string")
    if not isinstance(root.get("vectors"), dict):
        raise ValueError("'oracle_signal_v2.vectors' must be an object")

