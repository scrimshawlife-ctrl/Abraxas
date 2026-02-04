from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional, Tuple

ALLOWED_TOGGLES = {"oracle", "gates", "continuity", "consideration"}
VERBOSITY_LEVELS = {"low", "medium", "high"}
RISK_TOLERANCE_LEVELS = {"low", "medium", "high"}


def canonical_json_bytes(obj: Any) -> bytes:
    rendered = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return rendered.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prefs_hash_prefix(prefs: Dict[str, Any], length: int = 8) -> str:
    return sha256_hex(canonical_json_bytes(prefs))[:length]


def default_prefs() -> Dict[str, Any]:
    return {
        "verbosity": "medium",
        "focus": [],
        "risk_tolerance": "medium",
        "show": [],
        "hide": [],
    }


def _normalize_list(value: Any, max_items: int) -> List[str]:
    items: List[str] = []
    if isinstance(value, str):
        raw = value.split(",")
        items.extend(raw)
    elif isinstance(value, (list, set, tuple)):
        items.extend(list(value))
    elif value is not None:
        items.append(str(value))
    normalized = []
    for item in items:
        text = str(item).strip()
        if text:
            normalized.append(text)
    unique_sorted = sorted(set(normalized))
    return unique_sorted[:max_items]


def _validate_toggle_list(items: List[str]) -> List[str]:
    invalid = [item for item in items if item not in ALLOWED_TOGGLES]
    return invalid


def validate_prefs(prefs: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    allowed_keys = {"verbosity", "focus", "risk_tolerance", "show", "hide"}
    extra_keys = set(prefs.keys()) - allowed_keys
    if extra_keys:
        errors.append(f"unknown_keys:{sorted(extra_keys)}")

    verbosity = prefs.get("verbosity", "medium")
    if verbosity not in VERBOSITY_LEVELS:
        errors.append("invalid:verbosity")

    risk = prefs.get("risk_tolerance", "medium")
    if risk not in RISK_TOLERANCE_LEVELS:
        errors.append("invalid:risk_tolerance")

    focus = prefs.get("focus", [])
    show = prefs.get("show", [])
    hide = prefs.get("hide", [])
    if not isinstance(focus, list):
        errors.append("invalid:focus")
    if not isinstance(show, list):
        errors.append("invalid:show")
    if not isinstance(hide, list):
        errors.append("invalid:hide")

    invalid_show = _validate_toggle_list(show if isinstance(show, list) else [])
    invalid_hide = _validate_toggle_list(hide if isinstance(hide, list) else [])
    if invalid_show:
        errors.append(f"invalid:show:{sorted(invalid_show)}")
    if invalid_hide:
        errors.append(f"invalid:hide:{sorted(invalid_hide)}")

    return len(errors) == 0, errors


def normalize_prefs(prefs: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    prefs = prefs or {}
    extra_keys = set(prefs.keys()) - {"verbosity", "focus", "risk_tolerance", "show", "hide"}
    if extra_keys:
        raise ValueError(f"unknown_keys:{sorted(extra_keys)}")
    normalized = default_prefs()
    verbosity = prefs.get("verbosity", normalized["verbosity"])
    risk = prefs.get("risk_tolerance", normalized["risk_tolerance"])
    normalized["verbosity"] = verbosity
    normalized["risk_tolerance"] = risk
    normalized["focus"] = _normalize_list(prefs.get("focus", []), 5)
    normalized["show"] = _normalize_list(prefs.get("show", []), 10)
    normalized["hide"] = _normalize_list(prefs.get("hide", []), 10)

    ok, errors = validate_prefs(normalized)
    if not ok:
        raise ValueError(";".join(errors))
    return normalized


def apply_prefs_update(
    *,
    run: Any,
    new_prefs: Dict[str, Any],
    ledger,
    event_id: str,
    timestamp_utc: str,
) -> Dict[str, Any]:
    old_prefs = normalize_prefs(getattr(run, "prefs", None))
    normalized = normalize_prefs(new_prefs)
    run.prefs = normalized
    data = {
        "old_prefs_hash_prefix": prefs_hash_prefix(old_prefs),
        "new_prefs_hash_prefix": prefs_hash_prefix(normalized),
    }
    ledger.append(run.run_id, event_id, "prefs_update", timestamp_utc, data)
    return normalized


def prefs_show_sections(prefs: Dict[str, Any]) -> Dict[str, bool]:
    show = set(prefs.get("show", []))
    hide = set(prefs.get("hide", []))
    result: Dict[str, bool] = {}
    for section in ALLOWED_TOGGLES:
        if show:
            result[section] = section in show and section not in hide
        else:
            result[section] = section not in hide
    return result


def prefs_verbosity_limit(prefs: Dict[str, Any]) -> int:
    verbosity = prefs.get("verbosity", "medium")
    if verbosity == "low":
        return 3
    if verbosity == "high":
        return 7
    return 5


def prefs_focus_priority(lines: List[str], focus: List[str]) -> List[str]:
    if not focus:
        return lines

    def score(line: str) -> Tuple[int, str]:
        lowered = line.lower()
        for token in focus:
            if token.lower() in lowered:
                return (0, line)
        return (1, line)

    return [line for _, line in sorted([(score(line), line) for line in lines], key=lambda item: item[0])]


def emphasis_risk_flags(flags: List[str], prefs: Dict[str, Any]) -> List[str]:
    risk = prefs.get("risk_tolerance", "medium")
    if risk == "high":
        return []
    if risk == "low":
        return list(flags)
    emphasized = []
    for flag in flags:
        if flag.startswith("gate:") or flag.startswith("proposal_risk:"):
            emphasized.append(flag)
    return emphasized


def build_consideration_view(consideration: Dict[str, Any], prefs: Dict[str, Any]) -> Dict[str, Any]:
    limit = prefs_verbosity_limit(prefs)
    risk_flags = consideration.get("risk_flags", [])
    return {
        **consideration,
        "rationale_display": list(consideration.get("rationale", []))[:limit],
        "risk_flags_emphasis": emphasis_risk_flags(list(risk_flags), prefs),
    }
