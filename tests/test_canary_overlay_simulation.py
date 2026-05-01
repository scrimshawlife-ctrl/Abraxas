from __future__ import annotations

import copy

from abraxas.canary.sim_runner import build_canary_overlay_simulation_run
from abraxas.core.canonical import canonical_json


def _inputs(delta: float = 0.2):
    overlays = {"overlays": [{"overlay_id": "ov1", "source_key": "s1", "simulated_delta": delta}]}
    forecasts = {
        "forecasts": [
            {"forecast_id": "f1", "signal_sources": ["s1"], "source_families": []},
            {"forecast_id": "f2", "signal_sources": ["s2"], "source_families": ["s1"]},
        ]
    }
    outcomes = {"outcomes": []}
    scores = {"scores": [{"forecast_id": "f1", "brier_score": 0.2}, {"forecast_id": "f2", "brier_score": 0.3}]}
    return overlays, forecasts, outcomes, scores


def test_overlay_with_valid_scores_computes_simulation() -> None:
    o, f, out, s = _inputs(delta=0.1)
    run = build_canary_overlay_simulation_run(o, f, out, s)
    sim = run["simulations"][0]
    assert sim["status"] == "computed"
    assert sim["baseline_error"] == 0.25
    assert sim["simulated_error"] == 0.275


def test_no_matching_forecasts_not_computable() -> None:
    o, f, out, s = _inputs()
    o["overlays"][0]["source_key"] = "nomatch"
    run = build_canary_overlay_simulation_run(o, f, out, s)
    sim = run["simulations"][0]
    assert sim["status"] == "not_computable"
    assert sim["reason"] == "no_matching_forecasts"


def test_no_scores_not_computable() -> None:
    o, f, out, _ = _inputs()
    run = build_canary_overlay_simulation_run(o, f, out, {"scores": []})
    sim = run["simulations"][0]
    assert sim["status"] == "not_computable"
    assert sim["reason"] == "no_scores_available"


def test_improved_worsened_neutral() -> None:
    o, f, out, s = _inputs(delta=-0.5)
    assert build_canary_overlay_simulation_run(o, f, out, s)["simulations"][0]["improvement_direction"] == "improved"
    o, f, out, s = _inputs(delta=0.5)
    assert build_canary_overlay_simulation_run(o, f, out, s)["simulations"][0]["improvement_direction"] == "worsened"
    o, f, out, s = _inputs(delta=0.0)
    assert build_canary_overlay_simulation_run(o, f, out, s)["simulations"][0]["improvement_direction"] == "neutral"


def test_deterministic_output_overlay_id_authority_and_input_immutability() -> None:
    o, f, out, s = _inputs(delta=0.1)
    o0, f0, out0, s0 = copy.deepcopy(o), copy.deepcopy(f), copy.deepcopy(out), copy.deepcopy(s)

    run_a = build_canary_overlay_simulation_run(o, f, out, s)
    run_b = build_canary_overlay_simulation_run(o, f, out, s)

    assert canonical_json(run_a) == canonical_json(run_b)
    sim = run_a["simulations"][0]
    assert sim["overlay_id"] == "ov1"
    assert sim["authority"] == {
        "overlay_application": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }
    assert run_a["authority"] == sim["authority"]
    assert (o, f, out, s) == (o0, f0, out0, s0)
