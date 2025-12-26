"""
Tests for counterfactual report deltas.
"""

from pathlib import Path

import yaml

from abraxas.backtest.schema import BacktestCase, BacktestResult, BacktestStatus, Confidence
from abraxas.replay.counterfactual import run_counterfactual
from abraxas.replay.types import ReplayMask, ReplayMaskKind


def test_counterfactual_report_deltas(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cases_dir = tmp_path / "cases"
    cases_dir.mkdir()

    case = BacktestCase(
        case_id="case_cf_001",
        created_at="2025-12-26T00:00:00Z",
        description="test",
        forecast_ref={"run_id": "run", "artifact_path": "path", "tier": "enterprise"},
        evaluation_window={"start_ts": "2025-12-20T00:00:00Z", "end_ts": "2025-12-27T00:00:00Z"},
        triggers={"any_of": [], "all_of": []},
        scoring={"type": "binary", "weights": {"trigger": 1.0}},
        horizon="H72H",
        segment="core",
        narrative="N1_primary",
        topic_key="deepfake_pollution",
        forecast_delta_summary={
            "probs_before": {"branch_a": 0.4},
            "probs_after": {"branch_a": 0.5},
        },
    )
    case_path = cases_dir / "case_cf_001.yaml"
    case_path.write_text(yaml.safe_dump(case.model_dump(), sort_keys=False))

    portfolios_path = tmp_path / "portfolios.yaml"
    portfolios_path.write_text(
        yaml.safe_dump(
            {
                "portfolios": [
                    {
                        "portfolio_id": "cf_portfolio",
                        "horizons": ["H72H"],
                        "segments": ["core"],
                        "narratives": ["N1_primary"],
                        "case_selectors": [],
                        "protected": False,
                    }
                ]
            },
            sort_keys=False,
        )
    )

    baseline_result = BacktestResult(
        case_id="case_cf_001",
        status=BacktestStatus.HIT,
        score=1.0,
        confidence=Confidence.HIGH,
        forecast_scoring={"brier": 0.3, "log": 0.4},
        component_outcomes=[
            {
                "component_id": "FDR_SYNTH_COST_CURVE",
                "status": "HIT",
                "score_contrib": {"brier": 0.2},
            }
        ],
    )
    masked_result = BacktestResult(
        case_id="case_cf_001",
        status=BacktestStatus.HIT,
        score=1.0,
        confidence=Confidence.HIGH,
        forecast_scoring={"brier": 0.2, "log": 0.3},
        component_outcomes=[
            {
                "component_id": "FDR_SYNTH_COST_CURVE",
                "status": "MISS",
                "score_contrib": {"brier": 0.4},
            }
        ],
    )

    overrides_path = tmp_path / "overrides.yaml"
    overrides_path.write_text(
        yaml.safe_dump(
            {
                "baseline_results": [baseline_result.model_dump()],
                "masked_results": [masked_result.model_dump()],
            },
            sort_keys=False,
        )
    )

    mask = ReplayMask(
        mask_id="exclude_quarantined",
        kind=ReplayMaskKind.EXCLUDE_QUARANTINED,
        params={},
        description="exclude",
    )

    report = run_counterfactual(
        run_id="cf_run",
        portfolio_id="cf_portfolio",
        masks=[mask],
        cases_dir=str(cases_dir),
        portfolios_path=str(portfolios_path),
        fdr_path="data/forecast/decomposition/fdr_v0_1.yaml",
        overrides_path=str(overrides_path),
    )

    assert "probability_deltas" in report
    assert "score_deltas" in report["delta_summary"]
    assert report["delta_summary"]["score_deltas"]["forecast_scores"]["brier_avg"] is not None
