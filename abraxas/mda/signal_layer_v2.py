from __future__ import annotations

from typing import Any, Dict

from abraxas.mda.types import sha256_hex, stable_json_dumps


def mda_to_oracle_signal_v2(mda_out: Dict[str, Any]) -> Dict[str, Any]:
    """
    Project MDA output into an Oracle-facing Signal v2 envelope.

    Contract: `slice_hash` must be deterministic and depend only on the slice content.
    """
    slice_obj = {
        "envelope": mda_out.get("envelope", {}) or {},
        "domain_aggregates": mda_out.get("domain_aggregates", {}) or {},
        "dsp": mda_out.get("dsp", []) or [],
        "fusion_graph": mda_out.get("fusion_graph", {}) or {},
    }
    slice_hash = sha256_hex(stable_json_dumps(slice_obj))

    return {
        "oracle_signal_v2": {
            "meta": {
                "schema": "oracle_signal_v2@1",
                "slice_hash": slice_hash,
            },
            "slice": slice_obj,
        }
    }


def shallow_schema_check(sig: Dict[str, Any]) -> None:
    if not isinstance(sig, dict):
        raise AssertionError("Signal v2 must be a dict")
    osv2 = sig.get("oracle_signal_v2")
    if not isinstance(osv2, dict):
        raise AssertionError("Missing oracle_signal_v2")
    meta = osv2.get("meta")
    if not isinstance(meta, dict):
        raise AssertionError("Missing oracle_signal_v2.meta")
    if not isinstance(meta.get("slice_hash"), str) or not meta.get("slice_hash"):
        raise AssertionError("Missing oracle_signal_v2.meta.slice_hash")

