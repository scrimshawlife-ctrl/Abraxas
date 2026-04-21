from __future__ import annotations

import pytest

from abx.optional_dependencies import (
    dependency_available,
    dependency_status,
    load_optional_dependency,
    require_optional_dependency,
)
from abx.optional_jinja2 import jinja2_status, load_jinja2


def test_dependency_available_true_for_stdlib_json() -> None:
    assert dependency_available("json") is True
    assert load_optional_dependency("json") is not None


def test_dependency_available_false_for_missing_module() -> None:
    name = "module_that_does_not_exist_abc123"
    assert dependency_available(name) is False
    assert load_optional_dependency(name) is None


def test_require_optional_dependency_raises_with_structured_message() -> None:
    with pytest.raises(RuntimeError) as err:
        require_optional_dependency("module_that_does_not_exist_abc123", "render.preview")
    message = str(err.value)
    assert "dependency=module_that_does_not_exist_abc123" in message
    assert "feature=render.preview" in message
    assert "status=missing_optional_dependency" in message


def test_dependency_status_packet_shape_is_deterministic() -> None:
    packet = dependency_status(
        "module_that_does_not_exist_abc123",
        "render.preview",
        dependency_class="OPTIONAL_ADAPTER",
        authority_scope="presentation",
    )
    assert packet == {
        "dependency_name": "module_that_does_not_exist_abc123",
        "available": False,
        "dependency_class": "OPTIONAL_ADAPTER",
        "feature_name": "render.preview",
        "status": "missing_optional_dependency",
        "allowed_to_affect_truth": False,
        "fallback_policy": "bounded_degraded",
        "authority_scope": "presentation",
        "provenance": "abx.optional_dependencies.v0",
    }


def test_jinja2_status_and_loader_when_present() -> None:
    j2 = pytest.importorskip("jinja2")
    loaded = load_jinja2("report.render")
    assert loaded is j2
    packet = jinja2_status("report.render")
    assert packet["dependency_name"] == "jinja2"
    assert packet["available"] is True
    assert packet["allowed_to_affect_truth"] is False


def test_jinja2_missing_does_not_break_unrelated_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    import abx.optional_dependencies as optional_dependencies

    real_import_module = optional_dependencies.import_module

    def fake_import_module(name: str, package: str | None = None):  # type: ignore[override]
        if name == "jinja2":
            raise ModuleNotFoundError("simulated jinja2 missing")
        return real_import_module(name, package)

    monkeypatch.setattr(optional_dependencies, "import_module", fake_import_module)

    assert optional_dependencies.dependency_available("jinja2") is False
    with pytest.raises(RuntimeError):
        load_jinja2("template.render")
