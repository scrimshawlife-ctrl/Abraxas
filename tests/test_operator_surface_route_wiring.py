from __future__ import annotations

from pathlib import Path


def test_webpanel_operator_surface_routes_registered() -> None:
    src = Path("webpanel/routes/operator_surfaces_routes.py").read_text(encoding="utf-8")
    assert 'app.get("/runs/{run_id}/console"' in src
    assert 'app.get("/runs/compare"' in src
    assert 'app.get("/release/readiness"' in src
    assert 'app.get("/runs/{run_id}/evidence"' in src


def test_server_operator_surface_api_routes_registered() -> None:
    src = Path("server/routes.ts").read_text(encoding="utf-8")
    assert 'app.get("/api/operator/run/:runId"' in src
    assert 'app.get("/api/operator/compare/:runA/:runB"' in src
    assert 'app.get("/api/operator/release-readiness/:runId"' in src
    assert 'app.get("/api/operator/evidence/:runId"' in src
