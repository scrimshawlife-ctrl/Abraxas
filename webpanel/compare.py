from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple


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
