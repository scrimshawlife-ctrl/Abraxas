"""The console must not imply a model it does not have.

The operator console displays engine output, and until this change nothing on it said what produced that
output. This test pins two things:

1. The status the route builds is honest -- unconfigured means the offline path is named, and the standing
   note about custom inference is present.
2. The keys the template actually reads are the keys the route actually provides. That direction matters as
   much as the first: a template referencing `inference_status.foo` that the route never sets renders as an
   empty string, and an empty string in a provenance readout looks like "no model", which is exactly the
   ambiguity being removed.

The second check is static on purpose. Rendering the full console needs FastAPI and a real view object; this
runs everywhere and catches the drift that matters.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ABRAXAS = Path(__file__).resolve().parents[1]
TEMPLATE = ABRAXAS / "webpanel" / "templates" / "operator_console.html"


def _template_keys() -> set[str]:
    """Every `inference_status.<key>` the template reads."""
    text = TEMPLATE.read_text()
    return set(re.findall(r"inference_status\.([a-z_]+)", text))


def test_the_template_still_displays_the_inference_status() -> None:
    """The card must exist -- a template that stopped showing it would make this whole guard vacuous."""
    text = TEMPLATE.read_text()
    assert "<h2>Inference</h2>" in text, "the console no longer has an Inference card"
    assert _template_keys(), "the Inference card no longer reads anything from inference_status"


def test_the_route_provides_every_key_the_template_reads(monkeypatch) -> None:
    """Route and template must agree, in both directions."""
    pytest.importorskip("fastapi", reason="the webpanel routes need FastAPI")
    pytest.importorskip("jinja2", reason="the console template needs Jinja2")

    from webpanel.routes.operator_routes import _inference_status

    monkeypatch.delenv("ABX_INFERENCE_BASE_URL", raising=False)
    monkeypatch.delenv("ABX_INFERENCE_MODEL", raising=False)

    status = _inference_status()
    template_keys = _template_keys()

    missing = template_keys - set(status)
    assert not missing, (
        f"the template reads {sorted(missing)} from inference_status, but the route does not provide "
        f"{'it' if len(missing) == 1 else 'them'}; it would render as an empty string"
    )
    assert status, "the route provides no inference status at all"


def test_an_unconfigured_console_says_no_model_is_loaded(monkeypatch) -> None:
    """With no endpoint configured, the console must say so rather than stay silent."""
    pytest.importorskip("fastapi", reason="the webpanel routes need FastAPI")
    pytest.importorskip("jinja2", reason="the console template needs Jinja2")

    from webpanel.routes.operator_routes import _inference_status

    monkeypatch.delenv("ABX_INFERENCE_BASE_URL", raising=False)
    monkeypatch.delenv("ABX_INFERENCE_MODEL", raising=False)

    status = _inference_status()

    assert status["configured"] is False
    assert status["identity"] == "model-agnostic/offline-deterministic", status["identity"]
    assert "No model is loaded" in status["headline"]
    assert "custom inference coming soon" in status["note"], (
        "the standing note about custom inference is what tells an operator the difference between "
        "'no model yet' and 'a model evaluated this'"
    )
