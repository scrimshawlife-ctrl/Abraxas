from __future__ import annotations

from typing import Any, Dict, List, Tuple


MAX_NODES = 2000
MAX_REFS = 50
MAX_METRICS = 50
MAX_UNKNOWNS = 50


def _value_type(value: Any) -> Tuple[str, int | None]:
    if value is None:
        return "null", None
    if isinstance(value, bool):
        return "bool", None
    if isinstance(value, int):
        return "int", None
    if isinstance(value, float):
        return "float", None
    if isinstance(value, str):
        return "str", None
    if isinstance(value, list):
        return "list", len(value)
    if isinstance(value, dict):
        return "dict", len(value)
    return "str", None


def _is_ref_string(value: str) -> bool:
    if value.startswith("http://") or value.startswith("https://"):
        return True
    if (":" in value or "/" in value) and len(value) > 10:
        return True
    return False


def walk_payload(payload: Any) -> Dict[str, List[Dict[str, Any]]]:
    paths: List[Dict[str, Any]] = []
    numeric_metrics: List[Dict[str, Any]] = []
    string_refs: List[Dict[str, Any]] = []
    visited = 0

    def visit(value: Any, path: str) -> None:
        nonlocal visited
        if visited >= MAX_NODES:
            return
        visited += 1

        vtype, size = _value_type(value)
        entry: Dict[str, Any] = {"path": path, "type": vtype}
        if size is not None:
            entry["size"] = size
        paths.append(entry)

        if vtype in ("int", "float") and len(numeric_metrics) < MAX_METRICS:
            numeric_metrics.append({"path": path, "value": value})

        if vtype == "str" and isinstance(value, str) and _is_ref_string(value):
            if len(string_refs) < MAX_REFS:
                string_refs.append({"path": path, "value": value})

        if isinstance(value, dict):
            for key in sorted(value.keys()):
                next_path = f"{path}.{key}" if path else str(key)
                visit(value[key], next_path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                next_path = f"{path}[{index}]" if path else f"[{index}]"
                visit(item, next_path)

    visit(payload, "")

    paths_sorted = sorted(paths, key=lambda item: item["path"])
    metrics_sorted = sorted(numeric_metrics, key=lambda item: item["path"])
    refs_sorted = sorted(string_refs, key=lambda item: item["path"])
    return {
        "paths": paths_sorted,
        "numeric_metrics": metrics_sorted[:MAX_METRICS],
        "string_refs": refs_sorted[:MAX_REFS],
    }


def detect_unknowns(payload: Any) -> List[Dict[str, Any]]:
    unknowns: List[Dict[str, Any]] = []
    visited = 0

    def missing_like(value: str) -> bool:
        lowered = value.strip().lower()
        return lowered in {"", "n/a", "na", "unknown"}

    def visit(value: Any, path: str) -> None:
        nonlocal visited
        if visited >= MAX_NODES:
            return
        visited += 1

        if value is None:
            unknowns.append({"path": path, "reason": "null"})
        elif isinstance(value, list):
            if len(value) == 0:
                unknowns.append({"path": path, "reason": "empty_list"})
            for index, item in enumerate(value):
                next_path = f"{path}[{index}]" if path else f"[{index}]"
                visit(item, next_path)
        elif isinstance(value, dict):
            if len(value) == 0:
                unknowns.append({"path": path, "reason": "empty_dict"})
            for key in sorted(value.keys()):
                next_path = f"{path}.{key}" if path else str(key)
                visit(value[key], next_path)
        elif isinstance(value, str) and missing_like(value):
            unknowns.append({"path": path, "reason": "missing_like"})

    visit(payload, "")
    unknowns_sorted = sorted(unknowns, key=lambda item: item["path"])
    return unknowns_sorted[:MAX_UNKNOWNS]


def extract_claims_if_present(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    claims = payload.get("claims")
    if not isinstance(claims, list):
        return []
    out: List[Dict[str, Any]] = []
    for entry in claims:
        if isinstance(entry, dict):
            out.append(entry)
        if len(out) >= 25:
            break
    return out
