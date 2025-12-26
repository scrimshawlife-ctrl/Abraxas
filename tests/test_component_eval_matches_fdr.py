"""
Tests for component evaluation against FDR matches.
"""

import yaml

from abraxas.backtest.component_eval import eval_component_for_case
from abraxas.backtest.schema import BacktestCase
from abraxas.forecast.decomposition.registry import load_fdr, match_components


def test_component_eval_matches_fdr():
    registry = load_fdr("tests/fixtures/fdr/sample_fdr.yaml")
    with open("tests/fixtures/backtest/sample_cases_with_topic_keys.yaml", "r") as f:
        data = yaml.safe_load(f)
    case_data = data["cases"][0]
    case = BacktestCase(**case_data)

    matches = match_components(
        registry,
        topic_key=case.topic_key,
        horizon=case.horizon,
        domain=case.domain,
    )
    assert [c.component_id for c in matches] == ["FDR_SYNTH_COST_CURVE"]

    ledgers = {"integrity": [{"SSI": 0.8}]}
    outcome = eval_component_for_case(
        component=matches[0],
        case=case,
        events=[],
        ledgers=ledgers,
    )

    assert outcome.status == "HIT"
