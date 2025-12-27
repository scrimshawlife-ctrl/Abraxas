# Runtime validator (v0.1) — no deps, deterministic checks

from typing import Any, Dict, List, Tuple


def _is_type(val: Any, typ) -> bool:
    try:
        return isinstance(val, typ)
    except Exception:
        return False


def validate_payload(payload: Dict[str, Any], spec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    spec:
      {
        "required": {"field": type_or_tuple, ...},
        "optional": {"field": type_or_tuple, ...},
        "allow_extra": bool
      }
    """
    errors: List[str] = []
    required = spec.get("required", {}) or {}
    optional = spec.get("optional", {}) or {}
    allow_extra = bool(spec.get("allow_extra", True))

    for key, typ in required.items():
        if key not in payload:
            errors.append(f"missing_required:{key}")
        elif not _is_type(payload[key], typ):
            errors.append(
                f"type_mismatch:{key} expected={typ} got={type(payload[key])}"
            )

    for key, typ in optional.items():
        if key in payload and not _is_type(payload[key], typ):
            errors.append(
                f"type_mismatch:{key} expected={typ} got={type(payload[key])}"
            )

    if not allow_extra:
        allowed = set(required.keys()) | set(optional.keys())
        for key in payload.keys():
            if key not in allowed:
                errors.append(f"extra_field:{key}")

    return (len(errors) == 0), errors
