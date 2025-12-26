"""
Tests for portfolio case selection.
"""

from datetime import datetime, timezone

from abraxas.backtest.portfolio import select_cases_for_portfolio
from abraxas.backtest.schema import (
    BacktestCase,
    ForecastRef,
    EvaluationWindow,
    Triggers,
    TriggerSpec,
    TriggerKind,
    Scoring,
    ForecastBranchRef,
)


def _make_case(
    case_id: str,
    horizon: str,
    narrative: str,
    topic_keys: list[str],
    trigger_kind: TriggerKind,
    has_branch: bool = True,
    has_regime: bool = False,
) -> BacktestCase:
    return BacktestCase(
        case_id=case_id,
        created_at=datetime.now(timezone.utc),
        description="test",
        forecast_ref=ForecastRef(
            run_id="run",
            artifact_path="out/runs/run/reports/enterprise.json",
            tier="enterprise",
        ),
        evaluation_window=EvaluationWindow(
            start_ts=datetime(2025, 12, 20, 12, 0, 0, tzinfo=timezone.utc),
            end_ts=datetime(2025, 12, 23, 12, 0, 0, tzinfo=timezone.utc),
        ),
        triggers=Triggers(
            any_of=[TriggerSpec(kind=trigger_kind, params={"term": "test"})]
        ),
        scoring=Scoring(type="binary", weights={"trigger": 1.0}),
        forecast_branch_ref=ForecastBranchRef(
            ensemble_id="ens",
            branch_id="branch",
            predicted_p_at_ts="auto",
        ) if has_branch else None,
        horizon=horizon,
        segment="core",
        narrative=narrative,
        topic_keys=topic_keys,
        regime_outcome_ref={"id": "regime"} if has_regime else None,
    )


def test_portfolio_case_selection():
    cases = [
        _make_case(
            case_id="case_a",
            horizon="H72H",
            narrative="N1_primary",
            topic_keys=["propaganda_pressure"],
            trigger_kind=TriggerKind.TERM_SEEN,
            has_branch=True,
        ),
        _make_case(
            case_id="case_b",
            horizon="H1Y",
            narrative="N2_counter",
            topic_keys=["regime_shift"],
            trigger_kind=TriggerKind.INDEX_THRESHOLD,
            has_branch=False,
            has_regime=True,
        ),
        _make_case(
            case_id="case_c",
            horizon="H30D",
            narrative="N2_counter",
            topic_keys=["deepfake_pollution"],
            trigger_kind=TriggerKind.TERM_SEEN,
            has_branch=True,
        ),
    ]

    short_term = {
        "portfolio_id": "short_term_core",
        "horizons": ["H72H", "H30D"],
        "segments": ["core"],
        "narratives": ["N1_primary", "N2_counter"],
        "case_selectors": [
            {"kind": "has_forecast_branch_ref"},
            {"kind": "topic_key_in", "params": {"topic_keys": ["propaganda_pressure", "deepfake_pollution"]}},
        ],
    }

    long_horizon = {
        "portfolio_id": "long_horizon_integrity",
        "horizons": ["H1Y", "H5Y"],
        "segments": ["core"],
        "narratives": ["N1_primary", "N2_counter"],
        "case_selectors": [{"kind": "has_regime_outcome_ref"}],
    }

    slang = {
        "portfolio_id": "slang_term_emergence",
        "horizons": ["H72H", "H30D", "H90D"],
        "segments": ["core"],
        "narratives": ["N2_counter"],
        "case_selectors": [{"kind": "trigger_kind_in", "params": {"kinds": ["term_seen"]}}],
    }

    selected_short = select_cases_for_portfolio(cases, short_term)
    selected_long = select_cases_for_portfolio(cases, long_horizon)
    selected_slang = select_cases_for_portfolio(cases, slang)

    assert [case.case_id for case in selected_short] == ["case_a", "case_c"]
    assert [case.case_id for case in selected_long] == ["case_b"]
    assert [case.case_id for case in selected_slang] == ["case_c"]
