from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional, Tuple

from webpanel.gates import compute_gate_stack
from webpanel.oracle_output import extract_oracle_output


def canonical_json_bytes(obj: Any) -> bytes:
    rendered = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return rendered.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_hash(obj: Any) -> str:
    return sha256_hex(canonical_json_bytes(obj))


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _hash_prefix(value: Optional[str], length: int = 8) -> Optional[str]:
    if not value:
        return None
    return value[:length]


def _flatten_indicators(indicators: Any, prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(indicators, dict):
        for key in sorted(indicators.keys(), key=lambda k: str(k)):
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten_indicators(indicators[key], next_prefix))
        return out
    if isinstance(indicators, list):
        for idx, item in enumerate(indicators):
            label = None
            if isinstance(item, dict):
                label = item.get("path") or item.get("name")
            next_prefix = f"{prefix}.{label}" if label else f"{prefix}[{idx}]" if prefix else f"[{idx}]"
            if isinstance(item, dict) and "value" in item and len(item.keys()) <= 2 and label:
                out[next_prefix] = item.get("value")
                continue
            out.update(_flatten_indicators(item, next_prefix))
        return out
    key = prefix or "value"
    out[key] = indicators
    return out


def _normalize_flags(flags: Any) -> List[str]:
    items: List[str] = []
    if isinstance(flags, dict):
        for key, value in flags.items():
            if value:
                items.append(str(key))
            if isinstance(value, (list, set, tuple)):
                items.extend(str(item) for item in value)
            elif isinstance(value, str):
                items.append(value)
    elif isinstance(flags, list):
        items.extend(str(item) for item in flags)
    elif flags is not None:
        items.append(str(flags))
    return sorted({item for item in items if item.strip()})


def _oracle_delta(current: Optional[Dict[str, Any]], prev: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not current and not prev:
        return None
    present_change = bool(current) != bool(prev)
    current_flags = _normalize_flags(current.get("flags") if current else None)
    prev_flags = _normalize_flags(prev.get("flags") if prev else None)
    flags_added = sorted(set(current_flags) - set(prev_flags))
    flags_removed = sorted(set(prev_flags) - set(current_flags))

    indicator_changes: List[Dict[str, Any]] = []
    if current and prev:
        current_indicators = _flatten_indicators(current.get("indicators"))
        prev_indicators = _flatten_indicators(prev.get("indicators"))
        for path in sorted(set(current_indicators.keys()) | set(prev_indicators.keys())):
            left = prev_indicators.get(path)
            right = current_indicators.get(path)
            if left != right:
                indicator_changes.append({"path": path, "prev": left, "current": right})

    def _prov_value(oracle: Optional[Dict[str, Any]], key: str) -> Any:
        provenance = _safe_dict(oracle.get("provenance") if oracle else None)
        value = provenance.get(key)
        if isinstance(value, dict):
            return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return value

    prov_changed = {
        "input_hash": _prov_value(prev, "input_hash") != _prov_value(current, "input_hash"),
        "policy_hash": _prov_value(prev, "policy_hash") != _prov_value(current, "policy_hash"),
        "stability_status": _prov_value(prev, "stability_status") != _prov_value(
            current, "stability_status"
        ),
    }

    return {
        "present_change": present_change,
        "indicator_changes": indicator_changes[:20],
        "flags_added": flags_added[:20],
        "flags_removed": flags_removed[:20],
        "provenance_changed": prov_changed,
    }


def _gate_delta(current: Any, prev: Any, current_policy_hash: str) -> Dict[str, Any]:
    current_stack = compute_gate_stack(current, current_policy_hash)
    prev_stack = compute_gate_stack(prev, current_policy_hash) if prev is not None else []
    top_prev = prev_stack[0]["code"] if prev_stack else None
    top_now = current_stack[0]["code"] if current_stack else None
    prev_codes = {gate.get("code") for gate in prev_stack if gate.get("code")}
    current_codes = {gate.get("code") for gate in current_stack if gate.get("code")}
    added = sorted(current_codes - prev_codes)
    removed = sorted(prev_codes - current_codes)
    changes = [f"added:{code}" for code in added] + [f"removed:{code}" for code in removed]
    return {
        "top_gate_prev": top_prev,
        "top_gate_now": top_now,
        "changes": changes[:10],
    }


def _ledger_delta(current: Any, prev: Any) -> Dict[str, Any]:
    current_events = _safe_list(getattr(current, "ledger_events", None))[-50:]
    prev_events = _safe_list(getattr(prev, "ledger_events", None))[-50:] if prev else []

    def _event_key(event: Any) -> str:
        event_id = getattr(event, "event_id", None)
        if event_id:
            return str(event_id)
        return f"{getattr(event, 'timestamp_utc', '')}|{getattr(event, 'event_type', '')}"

    prev_keys = {_event_key(ev) for ev in prev_events}
    new_events = [ev for ev in current_events if _event_key(ev) not in prev_keys]
    new_event_types = sorted(
        {str(getattr(ev, "event_type", "")) for ev in new_events if getattr(ev, "event_type", None)}
    )
    return {
        "new_events_count": len(new_events),
        "new_event_types": new_event_types[:10],
    }


def _runplan_delta(current: Any, prev: Any) -> Dict[str, Any]:
    step_prev = getattr(prev, "current_step_index", None) if prev else None
    step_now = getattr(current, "current_step_index", None)
    changed = step_prev != step_now
    return {
        "step_index_prev": step_prev,
        "step_index_now": step_now,
        "changed": bool(changed),
    }


def build_continuity_report(
    current: Any,
    prev: Optional[Any],
    current_policy_hash: str,
) -> Dict[str, Any]:
    current_oracle = extract_oracle_output(current)
    prev_oracle = extract_oracle_output(prev) if prev else None

    oracle_delta = _oracle_delta(current_oracle, prev_oracle)
    gates_delta = _gate_delta(current, prev, current_policy_hash)
    ledger_delta = _ledger_delta(current, prev)
    runplan_delta = _runplan_delta(current, prev)

    summary_lines: List[str] = []
    if oracle_delta:
        if oracle_delta["present_change"]:
            summary_lines.append("oracle.present_change")
        if oracle_delta["flags_added"]:
            summary_lines.append(f"oracle.flags_added:{len(oracle_delta['flags_added'])}")
        if oracle_delta["flags_removed"]:
            summary_lines.append(f"oracle.flags_removed:{len(oracle_delta['flags_removed'])}")
    if gates_delta.get("top_gate_prev") != gates_delta.get("top_gate_now"):
        summary_lines.append(
            f"gates.top_changed:{gates_delta.get('top_gate_prev')}->{gates_delta.get('top_gate_now')}"
        )
    if ledger_delta["new_events_count"]:
        summary_lines.append(f"ledger.new_events:{ledger_delta['new_events_count']}")
    if runplan_delta["changed"]:
        summary_lines.append(
            f"runplan.step_index:{runplan_delta.get('step_index_prev')}->{runplan_delta.get('step_index_now')}"
        )
    summary_lines = sorted(summary_lines)[:7]

    risk_notes: List[str] = []
    current_gates = compute_gate_stack(current, current_policy_hash)
    for gate in current_gates:
        if gate.get("severity") == "block" and gate.get("code"):
            risk_notes.append(f"block:{gate.get('code')}")
    risk_notes = sorted(set(risk_notes))[:7]

    provenance = {
        "current_policy_hash_prefix": _hash_prefix(current_policy_hash),
        "prev_policy_hash_prefix": _hash_prefix(
            getattr(prev, "policy_hash_at_ingest", None) if prev else None
        ),
        "oracle_input_hash_prefix_current": _hash_prefix(
            _safe_dict(current_oracle.get("provenance")).get("input_hash") if current_oracle else None
        ),
        "oracle_input_hash_prefix_prev": _hash_prefix(
            _safe_dict(prev_oracle.get("provenance")).get("input_hash") if prev_oracle else None
        ),
        "oracle_policy_hash_prefix_current": _hash_prefix(
            _safe_dict(current_oracle.get("provenance")).get("policy_hash") if current_oracle else None
        ),
        "oracle_policy_hash_prefix_prev": _hash_prefix(
            _safe_dict(prev_oracle.get("provenance")).get("policy_hash") if prev_oracle else None
        ),
    }

    return {
        "run_id": getattr(current, "run_id", None),
        "prev_run_id": getattr(prev, "run_id", None) if prev else None,
        "deltas": {
            "oracle": oracle_delta,
            "gates": gates_delta,
            "ledger": ledger_delta,
            "runplan": runplan_delta,
        },
        "summary_lines": summary_lines,
        "risk_notes": risk_notes,
        "provenance": provenance,
    }
