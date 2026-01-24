from __future__ import annotations

from typing import Any, Dict, List


def _walk(obj: Any, prefix: str) -> List[str]:
    paths = []
    if isinstance(obj, dict):
        for key in sorted(obj.keys()):
            val = obj[key]
            path = f"{prefix}.{key}" if prefix else str(key)
            paths.extend(_walk(val, path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            paths.extend(_walk(item, f"{prefix}[{idx}]"))
    else:
        paths.append(prefix)
    return paths


def _has_key_path(obj: Any, key_path: str) -> bool:
    if not key_path:
        return False
    cur = obj
    for part in key_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    return True


def _find_forbidden_keys(obj: Any, keys: List[str]) -> List[str]:
    found = []
    paths = _walk(obj, "report")
    for path in paths:
        tail = path.split(".")[-1]
        if tail in keys:
            found.append(path)
    return sorted(set(found))


def lint_report_for_tier(report: Dict[str, Any], tier: str) -> List[str]:
    tier_norm = (tier or "psychonaut").lower()
    violations: List[str] = []

    forbidden_psy = [
        "verified_sub_anagrams",
        "clusters",
        "candidates",
        "pfdi_state",
        "pfdi_alerts",
        "enterprise_diagnostics",
        "run_id",
    ]
    forbidden_academic = [
        "candidates",
        "enterprise_diagnostics",
    ]
    forbidden_raw = ["url", "text"]

    if tier_norm == "psychonaut":
        for key_path in forbidden_psy:
            if _has_key_path(report, key_path):
                violations.append(f"report.{key_path} forbidden in psychonaut")
        for path in _find_forbidden_keys(report, forbidden_raw):
            violations.append(f"{path} forbidden in psychonaut")
        return sorted(set(violations))

    if tier_norm == "academic":
        for key_path in forbidden_academic:
            if _has_key_path(report, key_path):
                violations.append(f"report.{key_path} forbidden in academic")
        for path in _find_forbidden_keys(report, forbidden_raw):
            violations.append(f"{path} forbidden in academic")
        return sorted(set(violations))

    return []
