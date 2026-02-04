from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional

from webpanel.oracle_output import canonical_json_str, extract_oracle_output


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


def _proposal_id(proposal: Dict[str, Any]) -> str:
    return stable_hash(proposal)


def _rationale_from_oracle(oracle: Optional[Dict[str, Any]]) -> List[str]:
    if not oracle:
        return []
    lines: List[str] = []
    indicators = _flatten_indicators(oracle.get("indicators"))
    for path in sorted(indicators.keys())[:3]:
        value = indicators.get(path)
        lines.append(f"oracle.indicator.{path}={value}")
    flags = oracle.get("flags")
    if isinstance(flags, dict):
        for key in sorted(flags.keys())[:3]:
            if flags.get(key):
                lines.append(f"oracle.flag.{key}")
    elif isinstance(flags, list):
        for entry in sorted(str(x) for x in flags)[:3]:
            lines.append(f"oracle.flag.{entry}")
    return lines


def _rationale_from_gates(gates: List[Dict[str, Any]]) -> List[str]:
    lines = []
    for gate in gates:
        code = gate.get("code")
        message = gate.get("message")
        if code and message:
            lines.append(f"gate.{code}:{message}")
        elif code:
            lines.append(f"gate.{code}")
    return lines


def _rationale_from_ledger(run: Any) -> List[str]:
    events = getattr(run, "ledger_events", None)
    if not events:
        return []
    lines = []
    for event in list(events)[-20:]:
        event_type = getattr(event, "event_type", None)
        if event_type:
            lines.append(f"ledger.event:{event_type}")
    return lines


def _rationale_from_proposal(proposal: Dict[str, Any]) -> List[str]:
    lines = []
    kind = proposal.get("kind")
    title = proposal.get("title")
    if kind:
        lines.append(f"proposal.kind={kind}")
    if title:
        lines.append(f"proposal.title={title}")
    rationale = proposal.get("rationale")
    if isinstance(rationale, list):
        for entry in rationale:
            text = str(entry).strip()
            if text:
                lines.append(f"proposal.rationale={text}")
    return lines


def _normalize_rationale(entries: List[tuple[int, str]], limit: int = 7) -> List[str]:
    unique = {}
    for priority, text in entries:
        if not text:
            continue
        key = (priority, text)
        unique[key] = text
    ordered = sorted(unique.keys(), key=lambda item: (item[0], item[1]))
    return [unique[key] for key in ordered][:limit]


def _dependencies(proposal: Dict[str, Any], oracle: Optional[Dict[str, Any]]) -> List[str]:
    deps: List[str] = []
    required = proposal.get("required_gates")
    if isinstance(required, list):
        deps.extend(str(item) for item in required if str(item).strip())
    if oracle:
        deps.append("oracle_output")
    return sorted(set(deps))[:10]


def _counterfactuals(proposal: Dict[str, Any]) -> List[Dict[str, str]]:
    kind = proposal.get("kind") or "proposal"
    return [
        {
            "if_skipped": f"skip:{kind}",
            "likely_effect": "no action executed for proposal",
        }
    ]


def _risk_flags(proposal: Dict[str, Any], oracle: Optional[Dict[str, Any]], gates: List[Dict[str, Any]]) -> List[str]:
    flags: List[str] = []
    if oracle:
        flags.extend(sorted(_normalize_flag_list(oracle.get("flags"))))
    risk_notes = proposal.get("risk_notes")
    if isinstance(risk_notes, str) and risk_notes.strip():
        flags.append(f"proposal_risk:{risk_notes.strip()}")
    for gate in gates:
        code = gate.get("code")
        if code:
            flags.append(f"gate:{code}")
    return sorted(set(flags))[:10]


def _normalize_flag_list(flags: Any) -> List[str]:
    items: List[str] = []
    if isinstance(flags, dict):
        for key, value in flags.items():
            if value:
                items.append(str(key))
            if isinstance(value, (list, set, tuple)):
                for entry in value:
                    items.append(str(entry))
            elif isinstance(value, str):
                items.append(value)
    elif isinstance(flags, list):
        items.extend(str(item) for item in flags)
    elif flags is not None:
        items.append(str(flags))
    return [item for item in items if item.strip()]


def _evidence_refs(oracle: Optional[Dict[str, Any]]) -> List[str]:
    if not oracle:
        return []
    items = []
    for entry in _safe_list(oracle.get("evidence")):
        if isinstance(entry, dict):
            items.append(canonical_json_str(entry))
        else:
            items.append(str(entry))
    return sorted(items)[:20]


def build_consideration(
    run: Any,
    proposal: Dict[str, Any],
    oracle: Optional[Dict[str, Any]],
    gates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    proposal_id = _proposal_id(proposal)
    entries: List[tuple[int, str]] = []
    for line in _rationale_from_oracle(oracle):
        entries.append((1, line))
    for line in _rationale_from_gates(gates):
        entries.append((2, line))
    for line in _rationale_from_ledger(run):
        entries.append((3, line))
    for line in _rationale_from_proposal(proposal):
        entries.append((4, line))

    rationale = _normalize_rationale(entries, limit=7)
    deps = _dependencies(proposal, oracle)
    counterfactuals = _counterfactuals(proposal)[:5]
    risk_flags = _risk_flags(proposal, oracle, gates)
    evidence_refs = _evidence_refs(oracle)

    oracle_signal_id = oracle.get("signal_id") if oracle else None
    provenance = {
        "run_id": getattr(run, "run_id", None),
        "oracle_signal_id": oracle_signal_id,
        "input_hash_prefix": _hash_prefix(_safe_dict(oracle.get("provenance")).get("input_hash"))
        if oracle
        else None,
        "policy_hash_prefix": _hash_prefix(_safe_dict(oracle.get("provenance")).get("policy_hash"))
        if oracle
        else None,
        "gate_codes": [gate.get("code") for gate in gates if gate.get("code")][:10],
    }

    return {
        "proposal_id": proposal_id,
        "rationale": rationale,
        "dependencies": deps,
        "counterfactuals": counterfactuals,
        "risk_flags": risk_flags,
        "evidence_refs": evidence_refs,
        "provenance": provenance,
    }


def _hash_prefix(value: Optional[str], length: int = 8) -> Optional[str]:
    if not value:
        return None
    return value[:length]


def _extract_proposals(run: Any) -> List[Dict[str, Any]]:
    step_results = getattr(run, "step_results", [])
    for result in reversed(step_results or []):
        if isinstance(result, dict) and result.get("kind") == "propose_actions_v0":
            actions = result.get("actions")
            if isinstance(actions, list):
                return [action for action in actions if isinstance(action, dict)]
            return []
    last = getattr(run, "last_step_result", None)
    if isinstance(last, dict) and last.get("kind") == "propose_actions_v0":
        actions = last.get("actions")
        if isinstance(actions, list):
            return [action for action in actions if isinstance(action, dict)]
    return []


def build_considerations_for_run(
    run: Any,
    oracle: Optional[Dict[str, Any]] = None,
    gates: Optional[List[Dict[str, Any]]] = None,
    ledger_events: Optional[Iterable[Any]] = None,
) -> List[Dict[str, Any]]:
    if ledger_events is not None:
        setattr(run, "ledger_events", list(ledger_events))
    oracle = oracle if oracle is not None else extract_oracle_output(run)
    gates = gates or []
    proposals = _extract_proposals(run)
    considerations = []
    for proposal in proposals:
        considerations.append(build_consideration(run, proposal, oracle, gates))
    considerations = sorted(considerations, key=lambda item: item.get("proposal_id", ""))
    if ledger_events is not None and hasattr(run, "ledger_events"):
        try:
            delattr(run, "ledger_events")
        except Exception:
            pass
    return considerations
