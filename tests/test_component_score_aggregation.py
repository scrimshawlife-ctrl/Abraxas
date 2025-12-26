"""
Tests for component score aggregation.
"""

from abraxas.scoreboard.components import aggregate_component_outcomes


def test_component_score_aggregation():
    outcomes = [
        {
            "component_id": "COMP_A",
            "status": "HIT",
            "score_contrib": {"brier": 0.1},
        },
        {
            "component_id": "COMP_A",
            "status": "MISS",
            "score_contrib": {"brier": 0.3},
        },
        {
            "component_id": "COMP_A",
            "status": "UNKNOWN",
            "score_contrib": {},
        },
        {
            "component_id": "COMP_B",
            "status": "ABSTAIN",
            "score_contrib": {"coverage_rate": 1.0},
        },
    ]

    aggregated = aggregate_component_outcomes(outcomes)

    assert aggregated["COMP_A"]["n"] == 3
    assert aggregated["COMP_A"]["hit_rate"] == 0.5
    assert aggregated["COMP_A"]["brier_avg"] == 0.2
    assert aggregated["COMP_A"]["unknown_rate"] == 1 / 3

    assert aggregated["COMP_B"]["n"] == 1
    assert aggregated["COMP_B"]["coverage_rate"] == 1.0
    assert aggregated["COMP_B"]["abstain_rate"] == 1.0
