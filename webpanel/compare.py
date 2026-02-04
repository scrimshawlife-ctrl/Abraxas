from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from webpanel.policy import MAX_DIFF_METRICS, MAX_DIFF_PATHS, MAX_DIFF_REFS, MAX_DIFF_UNKNOWNS


def get_latest_step(run, kind: str) -> Optional[Dict[str, Any]]:
    for result in reversed(run.step_results):
        if isinstance(result, dict) and result.get("kind") == kind:
            return result
    return None


def diff_sets(
    left_list: List[Any],
    right_list: List[Any],
    key_fn: Callable[[Any], str],
) -> Dict[str, List[str]]:
    left_keys = {key_fn(item) for item in left_list}
    right_keys = {key_fn(item) for item in right_list}
    added = sorted(right_keys - left_keys)
    removed = sorted(left_keys - right_keys)
    common = sorted(left_keys & right_keys)
    return {"added": added, "removed": removed, "common": common}


def diff_numeric_metrics(
    left_metrics: List[Dict[str, Any]],
    right_metrics: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    left_map = {entry.get("path"): entry.get("value") for entry in left_metrics if "path" in entry}
    right_map = {entry.get("path"): entry.get("value") for entry in right_metrics if "path" in entry}
    all_paths = sorted(set(left_map.keys()) | set(right_map.keys()))
    diffs: List[Dict[str, Any]] = []
    for path in all_paths:
        left_val = left_map.get(path)
        right_val = right_map.get(path)
        try:
            delta = float(right_val) - float(left_val)
        except Exception:
            delta = None
        diffs.append({"path": path, "left": left_val, "right": right_val, "delta": delta})

    def sort_key(entry: Dict[str, Any]) -> Tuple[float, str]:
        delta = entry.get("delta")
        magnitude = abs(delta) if isinstance(delta, (int, float)) else -1.0
        return (-magnitude, entry.get("path") or "")

    return sorted(diffs, key=sort_key)


def extract_paths(extract: Optional[Dict[str, Any]]) -> List[str]:
    if not extract:
        return []
    paths = extract.get("paths")
    if isinstance(paths, list) and paths:
        return [str(path) for path in paths]
    topology = extract.get("keys_topology", {}) if isinstance(extract, dict) else {}
    sample_paths = topology.get("sample_paths")
    if isinstance(sample_paths, list):
        return [str(path) for path in sample_paths]
    return []


def safe_extract_fields(run) -> Dict[str, Any]:
    extract = get_latest_step(run, "extract_structure_v0")
    compress = get_latest_step(run, "compress_signal_v0")

    paths = sorted(extract_paths(extract))[:MAX_DIFF_PATHS]
    unknowns = extract.get("unknowns", []) if extract else []
    unknown_paths = sorted(
        [
            str(item.get("path") if isinstance(item, dict) else item)
            for item in unknowns
        ]
    )[:MAX_DIFF_UNKNOWNS]
    refs = extract.get("evidence_refs", []) if extract else []
    ref_entries = sorted(
        [
            {"path": item.get("path"), "value": item.get("value")}
            for item in refs
            if isinstance(item, dict)
        ],
        key=lambda item: f"{item.get('path')}|{item.get('value')}",
    )[:MAX_DIFF_REFS]
    metrics = extract.get("numeric_metrics", []) if extract else []
    metrics_sorted = sorted(
        [entry for entry in metrics if isinstance(entry, dict)],
        key=lambda item: str(item.get("path")),
    )

    return {
        "meta": {
            "tier": run.signal.tier,
            "lane": run.signal.lane,
            "invariance_status": run.signal.invariance_status,
            "provenance_status": run.signal.provenance_status,
            "drift_flags": list(run.signal.drift_flags),
            "rent_status": run.signal.rent_status,
        },
        "pause": {
            "pause_required": run.pause_required,
            "pause_reason": run.pause_reason,
        },
        "pressure": compress.get("plan_pressure") if compress else None,
        "extract": {
            "paths": paths,
            "unknowns": unknown_paths,
            "refs": ref_entries,
            "numeric_metrics": metrics_sorted[:MAX_DIFF_METRICS],
        },
    }


def compare_runs(left_run, right_run) -> Dict[str, Any]:
    left = safe_extract_fields(left_run)
    right = safe_extract_fields(right_run)

    paths_diff = diff_sets(left["extract"]["paths"], right["extract"]["paths"], lambda x: x)
    unknowns_diff = diff_sets(left["extract"]["unknowns"], right["extract"]["unknowns"], lambda x: x)
    refs_diff = diff_sets(
        left["extract"]["refs"],
        right["extract"]["refs"],
        lambda x: f"{x.get('path')}|{x.get('value')}" if isinstance(x, dict) else str(x),
    )
    numeric_diff = diff_numeric_metrics(
        left["extract"]["numeric_metrics"], right["extract"]["numeric_metrics"]
    )[:MAX_DIFF_METRICS]

    lineage_note = "direct supersession" if right_run.prev_run_id == left_run.run_id else None

    return {
        "left_run_id": left_run.run_id,
        "right_run_id": right_run.run_id,
        "meta": {"left": left["meta"], "right": right["meta"]},
        "pause": {"left": left["pause"], "right": right["pause"]},
        "pressure": {"left": left["pressure"], "right": right["pressure"]},
        "added_paths": paths_diff["added"][:MAX_DIFF_PATHS],
        "removed_paths": paths_diff["removed"][:MAX_DIFF_PATHS],
        "metric_deltas": numeric_diff,
        "unknowns_added": unknowns_diff["added"][:MAX_DIFF_UNKNOWNS],
        "unknowns_removed": unknowns_diff["removed"][:MAX_DIFF_UNKNOWNS],
        "refs_added": refs_diff["added"][:MAX_DIFF_REFS],
        "refs_removed": refs_diff["removed"][:MAX_DIFF_REFS],
        "lineage_note": lineage_note,
    }
