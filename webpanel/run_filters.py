from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from webpanel.oracle_output import extract_oracle_output


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _normalize_flags(flags: Any) -> set[str]:
    items: List[Any] = []
    if isinstance(flags, dict):
        items.extend(flags.keys())
        for value in flags.values():
            if isinstance(value, (list, set, tuple)):
                items.extend(value)
            elif isinstance(value, str):
                items.append(value)
    elif isinstance(flags, (list, set, tuple)):
        items.extend(list(flags))
    elif flags is not None:
        items.append(flags)
    out = set()
    for item in items:
        text = str(item).strip()
        if text:
            out.add(text)
    return out


def _parse_flags_param(params: Mapping[str, Any]) -> List[str]:
    flags: List[str] = []
    if hasattr(params, "getlist"):
        raw_list = params.getlist("flag")
    else:
        raw_list = [params.get("flag", "")] if isinstance(params, dict) else []
    for raw in raw_list:
        if raw is None:
            continue
        for item in str(raw).split(","):
            value = item.strip()
            if value:
                flags.append(value)
    return sorted(set(flags))


def parse_filter_params(params: Mapping[str, Any]) -> Dict[str, Any]:
    def _get(name: str, default: str = "any") -> str:
        raw = params.get(name, default) if isinstance(params, dict) else default
        if raw is None:
            return default
        value = str(raw).strip()
        return value if value else default

    has_oracle = _get("has_oracle")
    tier = _get("tier")
    lane = _get("lane")
    drift_class = _get("drift_class")
    evidence = _get("evidence")
    flags = _parse_flags_param(params)

    return {
        "has_oracle": has_oracle,
        "tier": tier,
        "lane": lane,
        "drift_class": drift_class,
        "evidence": evidence,
        "flags": flags,
        "flag_input": ", ".join(flags),
    }


def _drift_class_from_oracle(oracle: Dict[str, Any]) -> Optional[str]:
    provenance = _safe_dict(oracle.get("provenance"))
    stability = _safe_dict(provenance.get("stability_status"))
    drift = stability.get("drift_class")
    if isinstance(drift, str) and drift.strip():
        return drift.strip()
    return None


def _drift_class_from_stability(run: Any) -> Optional[str]:
    report = getattr(run, "stability_report", None)
    if not isinstance(report, dict):
        return None
    drift = report.get("drift_class")
    if isinstance(drift, str) and drift.strip():
        return drift.strip()
    return None


def _oracle_evidence_count(oracle: Optional[Dict[str, Any]]) -> Optional[int]:
    if not oracle:
        return None
    evidence = oracle.get("evidence")
    if isinstance(evidence, list):
        return len(evidence)
    return 0


def _run_sort_key_signal(run: Any) -> str:
    signal = getattr(run, "signal", None)
    if signal is None:
        return ""
    signal_id = getattr(signal, "signal_id", "")
    return str(signal_id)


def _run_sort_key_created(run: Any) -> str:
    created = getattr(run, "created_at_utc", "")
    return str(created)


def derive_run_fields(run: Any) -> Dict[str, Any]:
    oracle = extract_oracle_output(run)
    signal = getattr(run, "signal", None)
    tier = oracle.get("tier") if oracle else getattr(signal, "tier", None)
    lane = oracle.get("lane") if oracle else getattr(signal, "lane", None)
    drift_class = _drift_class_from_oracle(oracle) if oracle else None
    if drift_class is None:
        drift_class = _drift_class_from_stability(run)
    drift_class = drift_class or "unknown"
    flags = _normalize_flags(oracle.get("flags") if oracle else None)
    evidence_count = _oracle_evidence_count(oracle)
    return {
        "oracle": oracle,
        "has_oracle": bool(oracle),
        "tier": tier,
        "lane": lane,
        "drift_class": drift_class,
        "flags": flags,
        "evidence_count": evidence_count,
    }


def filter_runs(runs: List[Any], params: Mapping[str, Any]) -> List[Any]:
    parsed = parse_filter_params(params)
    has_oracle = parsed["has_oracle"]
    tier = parsed["tier"]
    lane = parsed["lane"]
    drift_class = parsed["drift_class"]
    evidence = parsed["evidence"]
    required_flags = parsed["flags"]

    filtered: List[Any] = []
    for run in runs:
        fields = derive_run_fields(run)
        oracle = fields["oracle"]
        if has_oracle == "yes" and not oracle:
            continue
        if has_oracle == "no" and oracle:
            continue
        if tier != "any" and fields["tier"] != tier:
            continue
        if lane != "any" and fields["lane"] != lane:
            continue
        if drift_class != "any" and fields["drift_class"] != drift_class:
            continue
        if required_flags:
            if not oracle:
                continue
            if not set(required_flags).issubset(fields["flags"]):
                continue
        if evidence != "any":
            if not oracle:
                continue
            count = fields["evidence_count"] or 0
            if evidence == "present" and count <= 0:
                continue
            if evidence == "missing" and count > 0:
                continue
        filtered.append(run)

    filtered = sorted(filtered, key=_run_sort_key_signal)
    filtered = sorted(filtered, key=_run_sort_key_created, reverse=True)
    return filtered


def build_run_view(run: Any) -> Dict[str, Any]:
    fields = derive_run_fields(run)
    signal = getattr(run, "signal", None)
    return {
        "run_id": getattr(run, "run_id", ""),
        "signal_id": getattr(signal, "signal_id", ""),
        "phase": getattr(run, "phase", None),
        "pause_required": getattr(run, "pause_required", False),
        "pause_reason": getattr(run, "pause_reason", None),
        "prev_run_id": getattr(run, "prev_run_id", None),
        "tier": fields["tier"],
        "lane": fields["lane"],
        "has_oracle": fields["has_oracle"],
        "drift_class": fields["drift_class"],
        "flags": sorted(fields["flags"]),
        "evidence_count": fields["evidence_count"],
    }
