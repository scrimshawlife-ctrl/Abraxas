from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from webpanel.oracle_output import extract_oracle_output


def normalize_oracle_flags(oracle_output: Optional[Dict[str, Any]]) -> set[str]:
    flags = oracle_output.get("flags") if oracle_output else None
    items: List[Any] = []
    if isinstance(flags, dict):
        for key, value in flags.items():
            if value:
                items.append(key)
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


def get_effective_tier(run: Any) -> Optional[str]:
    oracle = extract_oracle_output(run)
    if oracle and isinstance(oracle.get("tier"), str):
        return oracle.get("tier")
    signal = getattr(run, "signal", None)
    return getattr(signal, "tier", None)


def get_effective_lane(run: Any) -> Optional[str]:
    oracle = extract_oracle_output(run)
    if oracle and isinstance(oracle.get("lane"), str):
        return oracle.get("lane")
    signal = getattr(run, "signal", None)
    return getattr(signal, "lane", None)


def _drift_class_from_oracle(oracle: Dict[str, Any]) -> Optional[str]:
    provenance = oracle.get("provenance") if isinstance(oracle, dict) else None
    stability = provenance.get("stability_status") if isinstance(provenance, dict) else None
    drift = stability.get("drift_class") if isinstance(stability, dict) else None
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


def get_effective_drift_class(run: Any) -> str:
    oracle = extract_oracle_output(run)
    if oracle:
        drift = _drift_class_from_oracle(oracle)
        if drift:
            return drift
    drift = _drift_class_from_stability(run)
    return drift or "unknown"


def get_effective_evidence_state(run: Any) -> str:
    oracle = extract_oracle_output(run)
    if not oracle:
        return "unknown"
    evidence = oracle.get("evidence")
    if isinstance(evidence, list):
        return "present" if len(evidence) > 0 else "missing"
    return "missing"


def _run_sort_key_signal(run: Any) -> str:
    signal = getattr(run, "signal", None)
    if signal is None:
        return ""
    return str(getattr(signal, "signal_id", ""))


def _run_sort_key_created(run: Any) -> str:
    return str(getattr(run, "created_at_utc", ""))


def sort_runs_deterministically(runs: List[Any]) -> List[Any]:
    ordered = sorted(runs, key=_run_sort_key_signal)
    ordered = sorted(ordered, key=_run_sort_key_created, reverse=True)
    return ordered


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
        oracle = extract_oracle_output(run)
        if has_oracle == "yes" and not oracle:
            continue
        if has_oracle == "no" and oracle:
            continue
        if tier != "any" and get_effective_tier(run) != tier:
            continue
        if lane != "any" and get_effective_lane(run) != lane:
            continue
        if drift_class != "any" and get_effective_drift_class(run) != drift_class:
            continue
        if required_flags:
            if not oracle:
                continue
            flags = normalize_oracle_flags(oracle)
            if not set(required_flags).issubset(flags):
                continue
        if evidence != "any":
            if not oracle:
                continue
            if get_effective_evidence_state(run) != evidence:
                continue
        filtered.append(run)

    return sort_runs_deterministically(filtered)


def build_run_view(run: Any) -> Dict[str, Any]:
    oracle = extract_oracle_output(run)
    signal = getattr(run, "signal", None)
    return {
        "run_id": getattr(run, "run_id", ""),
        "signal_id": getattr(signal, "signal_id", ""),
        "phase": getattr(run, "phase", None),
        "pause_required": getattr(run, "pause_required", False),
        "pause_reason": getattr(run, "pause_reason", None),
        "prev_run_id": getattr(run, "prev_run_id", None),
        "tier": get_effective_tier(run),
        "lane": get_effective_lane(run),
        "has_oracle": bool(oracle),
        "drift_class": get_effective_drift_class(run),
    }
