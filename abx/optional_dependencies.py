from __future__ import annotations

from importlib import import_module
from typing import Any, Dict

# Launch dependency != truth authority:
# ENTRYPOINT_REQUIRED can fail the launch surface while unrelated imports remain safe.
FALLBACK_BY_CLASS = {
    "CORE_REQUIRED": "hard_setup_failure",
    "OPTIONAL_ADAPTER": "bounded_degraded",
    "ENTRYPOINT_REQUIRED": "launch_blocked_surface_only",
    "DEV_TEST_ONLY": "not_applicable",
    "LEGACY_DEPRECATED": "not_applicable",
}

MISSING_STATUS_BY_CLASS = {
    "CORE_REQUIRED": "missing_core_required_dependency",
    "OPTIONAL_ADAPTER": "missing_optional_dependency",
    "ENTRYPOINT_REQUIRED": "missing_entrypoint_dependency",
    "DEV_TEST_ONLY": "missing_dev_dependency",
    "LEGACY_DEPRECATED": "missing_legacy_dependency",
}


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
    return require_dependency(
        name=name,
        feature_name=feature_name,
        dependency_class=dependency_class,
    )


def require_dependency(
    *,
    name: str,
    feature_name: str,
    dependency_class: str,
) -> Any:
    module = load_optional_dependency(name)
    if module is not None:
        return module
    missing_status = MISSING_STATUS_BY_CLASS.get(dependency_class, "missing_optional_dependency")
    fallback_policy = FALLBACK_BY_CLASS.get(dependency_class, "bounded_degraded")
    raise RuntimeError(
        "Dependency missing for feature execution: "
        f"dependency={name}; feature={feature_name}; dependency_class={dependency_class}; "
        f"status={missing_status}; fallback={fallback_policy}"
    )


def dependency_status(
    name: str,
    feature_name: str,
    dependency_class: str,
    authority_scope: str,
    *,
    required_for_launch: bool = False,
    execution_boundary_role: str = "none",
    allowed_to_affect_truth: bool = False,
) -> Dict[str, Any]:
    available = dependency_available(name)
    fallback_policy = FALLBACK_BY_CLASS.get(dependency_class, "bounded_degraded")
    missing_status = MISSING_STATUS_BY_CLASS.get(dependency_class, "missing_optional_dependency")
    return {
        "dependency_name": name,
        "available": available,
        "dependency_class": dependency_class,
        "feature_name": feature_name,
        "status": "available" if available else missing_status,
        "required_for_launch": required_for_launch,
        "truth_authoritative": allowed_to_affect_truth,
        "allowed_to_affect_truth": allowed_to_affect_truth,
        "fallback_policy": fallback_policy if not available else "not_applicable",
        "authority_scope": authority_scope,
        "execution_boundary_role": execution_boundary_role,
        "provenance": "abx.optional_dependencies.v0",
    }
