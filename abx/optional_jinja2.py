from __future__ import annotations

from typing import Any

from abx.optional_dependencies import dependency_status, require_optional_dependency


def load_jinja2(feature_name: str = "template_rendering") -> Any:
    return require_optional_dependency("jinja2", feature_name)


def jinja2_status(feature_name: str = "template_rendering") -> dict:
    return dependency_status(
        name="jinja2",
        feature_name=feature_name,
        dependency_class="OPTIONAL_ADAPTER",
        authority_scope="presentation",
    )
