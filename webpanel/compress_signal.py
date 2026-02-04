from __future__ import annotations

from typing import Any, Dict, List


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def compute_plan_pressure(signal_meta: Dict[str, Any], ctx: Dict[str, Any], extracted: Dict[str, Any]) -> Dict[str, Any]:
    invariance_fail = 1 if signal_meta.get("invariance_status") == "fail" else 0
    provenance_gap = 1 if signal_meta.get("provenance_status") in ("partial", "missing") else 0
    drift_present = 1 if signal_meta.get("drift_flags") else 0
    unknowns_present = 1 if extracted.get("unknowns") or ctx.get("unknowns") else 0
    lane_shadow = 1 if signal_meta.get("lane") == "shadow" else 0

    score = 0.0
    score += 0.35 * invariance_fail
    score += 0.20 * provenance_gap
    score += 0.20 * drift_present
    score += 0.15 * unknowns_present
    score += 0.10 * lane_shadow
    score = round(_clamp(score), 3)

    return {
        "score": score,
        "components": {
            "invariance_fail": invariance_fail,
            "provenance_gap": provenance_gap,
            "drift_present": drift_present,
            "unknowns_present": unknowns_present,
            "lane_shadow": lane_shadow,
        },
    }


def pick_salient_metrics(numeric_metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def key_fn(entry: Dict[str, Any]) -> tuple:
        value = entry.get("value", 0)
        try:
            magnitude = abs(float(value))
        except Exception:
            magnitude = 0.0
        return (-magnitude, str(entry.get("path", "")))

    ordered = sorted(numeric_metrics, key=key_fn)
    return ordered[:10]


def build_uncertainty_map(extracted_unknowns: List[Dict[str, Any]], ctx_unknowns: List[Any]) -> Dict[str, List[str]]:
    buckets: Dict[str, List[str]] = {}

    def add(reason: str, path: str) -> None:
        if reason not in buckets:
            buckets[reason] = []
        buckets[reason].append(path)

    for entry in extracted_unknowns:
        if not isinstance(entry, dict):
            continue
        reason = entry.get("reason") or entry.get("reason_code") or "unknown"
        path = entry.get("path") or entry.get("region_id") or "unknown"
        add(reason, str(path))

    for entry in ctx_unknowns:
        if isinstance(entry, dict):
            reason = entry.get("reason") or entry.get("reason_code") or "unknown"
            path = entry.get("path") or entry.get("region_id") or "unknown"
            add(reason, f"context.{path}")
        else:
            add("unknown", f"context.{entry}")

    for reason in list(buckets.keys()):
        buckets[reason] = sorted(buckets[reason])[:20]
    return dict(sorted(buckets.items(), key=lambda item: item[0]))


def classify_refs(evidence_refs: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    urls: List[str] = []
    ids: List[str] = []
    for entry in evidence_refs:
        if not isinstance(entry, dict):
            continue
        path = str(entry.get("path", ""))
        value = str(entry.get("value", ""))
        if value.startswith("http://") or value.startswith("https://"):
            urls.append(path)
        else:
            ids.append(path)
    return {
        "url": sorted(urls),
        "id_like": sorted(ids),
    }


def recommended_mode(signal_meta: Dict[str, Any], pressure_score: float) -> str:
    if signal_meta.get("lane") == "shadow":
        return "observe_only"
    if pressure_score >= 0.55:
        return "clarify"
    return "present_options"


def next_questions(signal_meta: Dict[str, Any], extracted: Dict[str, Any], uncertainty_map: Dict[str, List[str]]) -> List[str]:
    questions: List[str] = []

    if signal_meta.get("invariance_status") != "pass":
        questions.append("Was invariance evaluated? If yes, provide result artifacts.")

    if signal_meta.get("provenance_status") in ("partial", "missing"):
        candidates = []
        for reason in sorted(uncertainty_map.keys()):
            candidates.extend(uncertainty_map[reason])
        for path in candidates[:2]:
            questions.append(f"Provide evidence/provenance for: {path}")

    if signal_meta.get("drift_flags"):
        questions.append("Which drift flags require follow-up?")

    for reason in sorted(uncertainty_map.keys()):
        label = reason.replace("_", " ")
        for path in uncertainty_map[reason]:
            if len(questions) >= 6:
                break
            questions.append(f"Clarify {label} field: {path}")
        if len(questions) >= 6:
            break

    trimmed: List[str] = []
    for question in questions:
        trimmed.append(question[:120])
        if len(trimmed) >= 6:
            break
    return trimmed
