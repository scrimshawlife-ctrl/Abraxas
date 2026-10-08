from __future__ import annotations

import importlib.util

import pytest


@pytest.mark.skipif(importlib.util.find_spec("jinja2") is None, reason="jinja2 not installed")
def test_webpanel_boot_and_template_compile():
    try:
        from fastapi.testclient import TestClient
    except Exception as exc:
        pytest.skip(f"fastapi TestClient unavailable: {exc}")

    from webpanel import app as webpanel_app
    from webpanel.panel_context import templates_factory

    # The template store moved to webpanel/panel_context.py as templates_factory();
    # this test still referenced webpanel_app._templates(), which no longer exists.
    # The test was the stale side, not the app -- the assertion below (a real GET to
    # "/" returning 200 with "Run" in the body) is the part that matters and is
    # unchanged.
    template = templates_factory().env.get_template("run.html")
    assert template is not None

    client = TestClient(webpanel_app.app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Run" in response.text
