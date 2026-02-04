from __future__ import annotations

from fastapi.testclient import TestClient

from webpanel import app as webpanel_app


def test_prev_run_id_prefill():
    client = TestClient(webpanel_app.app)
    response = client.get("/?prev_run_id=abc")
    assert response.status_code == 200
    assert 'name="prev_run_id"' in response.text
    assert 'value="abc"' in response.text
