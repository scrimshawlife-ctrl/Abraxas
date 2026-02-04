from __future__ import annotations

from fastapi.testclient import TestClient

from webpanel import app as webpanel_app


def test_lan_banner_visible(monkeypatch):
    monkeypatch.setenv("ABX_PANEL_HOST", "0.0.0.0")
    client = TestClient(webpanel_app.app)
    response = client.get("/")
    assert response.status_code == 200
    assert "LAN EXPOSED" in response.text


def test_lan_banner_hidden(monkeypatch):
    monkeypatch.setenv("ABX_PANEL_HOST", "127.0.0.1")
    client = TestClient(webpanel_app.app)
    response = client.get("/")
    assert response.status_code == 200
    assert "LAN EXPOSED" not in response.text
