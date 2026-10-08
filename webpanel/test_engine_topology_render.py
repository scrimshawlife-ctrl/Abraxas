"""The card must be on the console page, and the states must LOOK different.

A data model that renders identically for planned and active has not fixed anything -- the
operator still cannot tell an intended absence from a broken engine.
"""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def client():
    from webpanel.app import app

    return TestClient(app)


class TestCardIsOnThePage:
    def test_console_page_mentions_engines(self, client):
        r = client.get("/operator")
        assert r.status_code == 200
        body = r.text
        # before this work: `grep -ci engine operator_console.html` returned 1, and 0 in the
        # view module. The page must now show the topology by name.
        assert "Engine Topology" in body, "the topology card is not rendering"
        assert "athanor" in body
        assert "aether" in body

    def test_aether_is_labelled_planned_not_broken(self, client):
        body = client.get("/operator").text
        # the word must appear, so an operator reading the page knows the absence is by
        # design rather than an outage
        lowered = body.lower()
        assert "planned" in lowered
        assert "by design" in lowered or "not built" in lowered

    def test_states_are_visually_distinct(self, client):
        """The counterfactual: planned and active must not carry the same CSS class."""
        body = client.get("/operator").text
        assert 'class="card' in body  # the existing idiom is still in use
        assert ("state-active" in body) and ("state-planned" in body)


class TestUnaffectedSurfaces:
    def test_other_pages_still_render(self, client):
        """The topology read must not break pages that do not use it."""
        for path in ("/", "/operator"):
            assert client.get(path).status_code == 200, path
