from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, Optional

from webpanel.policy import MAX_DIFF_UNKNOWNS


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_hash(obj: Any) -> str:
    return sha256_hex(canonical_json_bytes(obj))


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _coerce_optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _normalize_unknowns(raw_unknowns: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for entry in _safe_list(raw_unknowns):
        if hasattr(entry, "model_dump"):
            entry = entry.model_dump()
        if isinstance(entry, dict):
            region_id = entry.get("region_id") or entry.get("path")
            reason_code = entry.get("reason_code") or entry.get("reason")
            notes = entry.get("notes")
        else:
            region_id = entry
            reason_code = None
            notes = None
        if region_id is None and reason_code is None and notes is None:
            continue
        item: Dict[str, Any] = {
            "region_id": _coerce_optional_str(region_id),
            "reason_code": _coerce_optional_str(reason_code),
        }
        if notes is not None:
            item["notes"] = _coerce_optional_str(notes)
        out.append(item)
    out_sorted = sorted(
        out,
        key=lambda item: (
            item.get("region_id") or "",
            item.get("reason_code") or "",
            item.get("notes") or "",
        ),
    )
    return out_sorted[:MAX_DIFF_UNKNOWNS]


def _extract_signal(run_or_signal: Any) -> Any:
    if isinstance(run_or_signal, dict) and "signal" in run_or_signal:
        return run_or_signal.get("signal")
    if hasattr(run_or_signal, "signal"):
        return getattr(run_or_signal, "signal")
    return run_or_signal


def _extract_unknowns(run_or_signal: Any) -> List[Dict[str, Any]]:
    if hasattr(run_or_signal, "context"):
        context = getattr(run_or_signal, "context")
        unknowns = getattr(context, "unknowns", [])
        return _normalize_unknowns(unknowns)
    if isinstance(run_or_signal, dict):
        context = run_or_signal.get("context")
        if isinstance(context, dict):
            return _normalize_unknowns(context.get("unknowns"))
        return _normalize_unknowns(
            run_or_signal.get("not_computable_regions") or run_or_signal.get("unknowns")
        )
    if hasattr(run_or_signal, "not_computable_regions"):
        return _normalize_unknowns(getattr(run_or_signal, "not_computable_regions"))
    return []


def build_input_envelope_for_hash(run_or_signal: Any) -> Dict[str, Any]:
    signal = _extract_signal(run_or_signal)
    if hasattr(signal, "model_dump"):
        signal_data = signal.model_dump()
    elif isinstance(signal, dict):
        signal_data = signal
    else:
        signal_data = {}

    drift_flags = _safe_list(signal_data.get("drift_flags"))
    drift_flags_norm = sorted(str(flag) for flag in drift_flags if str(flag).strip())

    metadata = {
        "tier": signal_data.get("tier"),
        "lane": signal_data.get("lane"),
        "provenance_status": signal_data.get("provenance_status"),
        "invariance_status": signal_data.get("invariance_status"),
        "drift_flags": drift_flags_norm,
    }

    payload = signal_data.get("payload")
    if payload is None:
        payload = {}

    envelope: Dict[str, Any] = {
        "payload": payload,
        "metadata": metadata,
    }
    unknowns = _extract_unknowns(run_or_signal)
    if unknowns:
        envelope["context"] = {"unknowns": unknowns}
    return envelope


def build_oracle_output_v2(
    *,
    signal_id: str,
    tier: str,
    lane: str,
    indicators: Mapping[str, Any],
    evidence: Optional[List[Any]],
    provenance: Mapping[str, Any],
    missing_inputs: Optional[List[str]] = None,
    drift_class: str = "none",
) -> Dict[str, Any]:
    evidence_items = list(evidence or [])
    missing = sorted(
        {str(item) for item in (missing_inputs or []) if str(item).strip()}
    )

    suppressed = False
    not_computable: Optional[Dict[str, Any]] = None
    if missing:
        suppressed = True
        not_computable = {"reason": "missing_inputs", "missing_inputs": missing}
    if drift_class and drift_class != "none":
        suppressed = True
        not_computable = {"reason": f"drift_class={drift_class}"}
        if missing:
            not_computable["missing_inputs"] = missing

    flags: Dict[str, Any] = {"suppressed": suppressed}
    if not_computable is not None:
        flags["not_computable"] = not_computable

    return {
        "signal_id": signal_id,
        "tier": tier,
        "lane": lane,
        "indicators": dict(indicators),
        "evidence": evidence_items,
        "flags": flags,
        "provenance": dict(provenance),
    }
