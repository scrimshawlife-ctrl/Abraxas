from __future__ import annotations

from importlib import import_module
from typing import Any, Dict


def dependency_available(name: str) -> bool:
    module = load_optional_dependency(name)
    return module is not None


def load_optional_dependency(name: str) -> Any | None:
    try:
        return import_module(name)
    except Exception:
        return None


def require_optional_dependency(
    name: str,
    feature_name: str,
    *,
    dependency_class: str = "OPTIONAL_ADAPTER",
) -> Any:
    module = load_optional_dependency(name)
    if module is not None:
        return module
    raise RuntimeError(
        "Optional dependency missing for feature execution: "
        f"dependency={name}; feature={feature_name}; dependency_class={dependency_class}; "
        "status=missing_optional_dependency; fallback=bounded_degraded"
    )


def dependency_status(
    name: str,
    feature_name: str,
    dependency_class: str,
    authority_scope: str,
) -> Dict[str, Any]:
    available = dependency_available(name)
    return {
        "dependency_name": name,
        "available": available,
        "dependency_class": dependency_class,
        "feature_name": feature_name,
        "status": "available" if available else "missing_optional_dependency",
        "allowed_to_affect_truth": False,
        "fallback_policy": "bounded_degraded" if not available else "not_applicable",
        "authority_scope": authority_scope,
        "provenance": "abx.optional_dependencies.v0",
    }
