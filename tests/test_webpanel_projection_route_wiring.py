from __future__ import annotations

from pathlib import Path


def test_webpanel_runs_route_uses_canonical_operator_projection_summary() -> None:
    src = Path("webpanel/routes/runs_routes.py").read_text(encoding="utf-8")

    assert "from abx.operator_projection import build_operator_projection_summary" in src
    assert "operator_projection_summary = build_operator_projection_summary(run.run_id).to_dict()" in src
    assert 'app.get("/runs/{run_id}/projection.json")(ui_projection_json)' in src
