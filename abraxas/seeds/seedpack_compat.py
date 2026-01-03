"""Seedpack compatibility shims (v0.1 -> v0.2)."""

from __future__ import annotations

from typing import Any, Dict


def normalize_seedpack(seedpack: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize older seedpacks to v0.2 shape deterministically."""
    sp = dict(seedpack or {})
    schema = str(sp.get("schema_version") or "")
    if "frames" in sp and isinstance(sp["frames"], list):
        if not sp.get("schema_version"):
            sp["schema_version"] = "seedpack.v0.2"
        return sp
    if schema == "seedpack.v0.1" and "records" in sp and isinstance(sp["records"], list):
        sp["frames"] = sp["records"]
        sp.pop("records", None)
        sp["schema_version"] = "seedpack.v0.2"
        prov = sp.get("provenance") or {}
        if isinstance(prov, dict):
            prov = dict(prov)
            prov["compat_transform"] = "v0.1_records_to_v0.2_frames"
            sp["provenance"] = prov
        return sp
    return sp
