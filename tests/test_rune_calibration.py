"""Goldens A/B for RUNE.CALIBRATION Shadow typed stub."""

from __future__ import annotations

import ast
from pathlib import Path

from abraxas.runes.operators.calibration import (
    CATEGORY,
    DECLARED_DEPENDENCIES,
    INFLUENCE_POLICY,
    LANE,
    RUNE_ID,
    CalibrationResult,
    activates_live_forecast_scoring,
    apply_calibration,
    calibrate,
    implements_forecast_score,
    metrics_from_emitted_artifacts,
)
from abraxas.runes.registry import describe_rune
from abx.lifecycle_policy import enforce_lane_policy
from abx.rune_contracts import get_abx_rune_contract

_LIFECYCLES = [
    {
        "id": "fl-1",
        "horizon": "7d",
        "resolution": "resolved",
        "outcome": "hit",
    },
    {
        "id": "fl-2",
        "horizon": "7d",
        "resolution": "resolved",
        "outcome": "miss",
    },
]
_SCORES = [
    {"id": "fs-1", "horizon": "7d", "resolution": "resolved"},
    {"id": "fs-2", "horizon": "7d", "resolution": "resolved"},
]
_HORIZON = {"id": "hs-1", "horizon": "7d", "bands": ["7d"]}


def _calibrate(lifecycles=_LIFECYCLES, scores=_SCORES, horizon=_HORIZON, **kwargs):
    return calibrate(lifecycles, scores, horizon, **kwargs)


def test_golden_a_determinism_identical_payloads() -> None:
    first = _calibrate(seed=7, run_id="CALIBRATION-A")
    second = _calibrate(seed=7, run_id="CALIBRATION-A")
    assert first.rune_id == "RUNE.CALIBRATION"
    assert first.rune_id == RUNE_ID
    assert first.model_dump() == second.model_dump()
    assert first.provenance.input_hash == second.provenance.input_hash
    assert first.provenance.output_hash == second.provenance.output_hash
    assert first.lane == "SHADOW"
    assert first.lane == LANE
    assert first.influence_policy == "NONE"
    assert first.influence_policy == INFLUENCE_POLICY
    assert first.category == "VALIDATE"
    assert first.category == CATEGORY
    assert first.calibration_incidents is None
    assert first.live_scoring_activated is False
    assert first.forecast_mutation is None
    assert first.forecast_weights is None
    assert first.calibration_report is not None
    assert first.performance_drift is not None
    assert first.horizon_metrics is not None
    assert first.calibration_report.report_id is None
    assert first.calibration_report.incidents is None
    assert first.calibration_report.score is None
    assert first.calibration_report.live_scoring_activated is False
    assert first.performance_drift.magnitude is None
    assert first.performance_drift.direction is None
    assert first.horizon_metrics.coverage is None
    assert first.horizon_metrics.score is None
    assert first.calibration_report.status == "NOT_COMPUTABLE"
    assert first.performance_drift.status == "NOT_COMPUTABLE"
    assert first.horizon_metrics.status == "NOT_COMPUTABLE"
    assert "NOT_COMPUTABLE" in first.not_computable_flags
    assert "metric_not_computable" in first.not_computable_flags
    assert first.provenance.confidence is None
    assert first.provenance.timestamp is None


def test_golden_a_metrics_recomputable_from_emitted_artifacts_only() -> None:
    first = _calibrate(seed=7, run_id="CALIBRATION-A-METRICS")
    second = _calibrate(seed=7, run_id="CALIBRATION-A-METRICS")
    left = metrics_from_emitted_artifacts(
        first.calibration_report,
        first.performance_drift,
        first.horizon_metrics,
    )
    right = metrics_from_emitted_artifacts(
        second.calibration_report,
        second.performance_drift,
        second.horizon_metrics,
    )
    assert left.model_dump() == right.model_dump()
    assert left.artifacts_hash == right.artifacts_hash
    assert left.calibration_score is None
    assert left.drift_magnitude is None
    assert left.horizon_coverage is None
    assert left.incidents is None
    assert left.status == "NOT_COMPUTABLE"
    assert left.metric_not_computable is True
    assert left.live_scoring_activated is False


def test_golden_a_same_artifacts_same_metrics_across_unrelated_inputs() -> None:
    left = _calibrate(seed=1, run_id="CAL-LEFT")
    right = _calibrate(seed=99, run_id="CAL-RIGHT")
    assert left.calibration_report.model_dump() == right.calibration_report.model_dump()
    assert left.performance_drift.model_dump() == right.performance_drift.model_dump()
    assert left.horizon_metrics.model_dump() == right.horizon_metrics.model_dump()
    left_metrics = metrics_from_emitted_artifacts(
        left.calibration_report,
        left.performance_drift,
        left.horizon_metrics,
    )
    right_metrics = metrics_from_emitted_artifacts(
        right.calibration_report,
        right.performance_drift,
        right.horizon_metrics,
    )
    assert left_metrics.model_dump() == right_metrics.model_dump()
    assert left.provenance.input_hash != right.provenance.input_hash
    assert left.calibration_incidents is None
    assert right.calibration_incidents is None


def test_golden_a_event_order_is_part_of_identity() -> None:
    left = _calibrate(_LIFECYCLES, _SCORES, _HORIZON)
    right = _calibrate(list(reversed(_LIFECYCLES)), _SCORES, _HORIZON)
    assert left.provenance.input_hash != right.provenance.input_hash
    assert left.calibration_report is not None
    assert left.calibration_report.score is None
    assert right.calibration_report is not None
    assert right.calibration_report.score is None
    assert left.live_scoring_activated is False
    assert right.live_scoring_activated is False


def test_golden_b_null_discipline_missing_inputs() -> None:
    missing_cycles = calibrate(None, _SCORES, _HORIZON)
    missing_scores = calibrate(_LIFECYCLES, None, _HORIZON)
    missing_horizon = calibrate(_LIFECYCLES, _SCORES, None)
    for result in (missing_cycles, missing_scores, missing_horizon):
        assert result.calibration_report is None
        assert result.performance_drift is None
        assert result.horizon_metrics is None
        assert result.calibration_incidents is None
        assert result.live_scoring_activated is False
        assert "NOT_COMPUTABLE" in result.not_computable_flags
        assert "metric_not_computable" in result.not_computable_flags
        assert result.provenance.confidence is None
    assert "missing_resolution_data" in missing_cycles.not_computable_flags
    assert "missing_resolution_data" in missing_scores.not_computable_flags


def test_golden_b_null_discipline_missing_resolution_data() -> None:
    result = calibrate(
        [{"id": "fl-1", "horizon": "7d"}],
        [{"id": "fs-1", "horizon": "7d"}],
        {"id": "hs-1", "horizon": "7d"},
    )
    assert result.calibration_report is None
    assert result.performance_drift is None
    assert result.horizon_metrics is None
    assert result.calibration_incidents is None
    flags = result.not_computable_flags
    assert "NOT_COMPUTABLE" in flags
    assert "metric_not_computable" in flags
    assert "missing_resolution_data" in flags


def test_golden_b_null_discipline_horizon_mismatch() -> None:
    result = calibrate(
        [
            {
                "id": "fl-1",
                "horizon": "7d",
                "resolution": "resolved",
                "outcome": "hit",
            }
        ],
        [{"id": "fs-1", "horizon": "7d", "resolution": "resolved"}],
        {"id": "hs-1", "horizon": "30d", "bands": ["30d"]},
    )
    assert result.calibration_report is None
    assert result.performance_drift is None
    assert result.horizon_metrics is None
    assert result.calibration_incidents is None
    assert result.live_scoring_activated is False
    flags = result.not_computable_flags
    assert "NOT_COMPUTABLE" in flags
    assert "metric_not_computable" in flags
    assert "horizon_mismatch" in flags


def test_golden_b_null_discipline_weak_placeholder() -> None:
    result = calibrate(
        [{"status": "NOT_COMPUTABLE"}, {"placeholder": True}],
        [{"status": "NOT_COMPUTABLE"}],
        {"status": "NOT_COMPUTABLE"},
    )
    assert result.calibration_report is None
    assert result.performance_drift is None
    assert result.horizon_metrics is None
    assert result.calibration_incidents is None
    flags = result.not_computable_flags
    assert "NOT_COMPUTABLE" in flags
    assert "metric_not_computable" in flags
    assert "placeholder_or_weak_input" in flags
    assert "missing_resolution_data" in flags


def test_golden_b_empty_and_unparseable() -> None:
    empty = calibrate([], [], {})
    junk = calibrate("not-lifecycles", "not-scores", "not-horizon")
    for result in (empty, junk):
        assert result.calibration_report is None
        assert result.performance_drift is None
        assert result.horizon_metrics is None
        assert result.calibration_incidents is None
        assert result.live_scoring_activated is False
        assert "NOT_COMPUTABLE" in result.not_computable_flags
        assert "metric_not_computable" in result.not_computable_flags


def test_no_wall_clock_without_caller_timestamp() -> None:
    result = _calibrate(timestamp=None)
    assert result.provenance.timestamp is None


def test_never_activates_live_forecast_scoring() -> None:
    result = _calibrate()
    assert activates_live_forecast_scoring() is False
    assert implements_forecast_score() is False
    assert result.live_scoring_activated is False
    assert result.forecast_mutation is None
    assert result.forecast_weights is None
    assert result.calibration_incidents is None


def test_does_not_import_forecast_scoring_or_implement_forecast_score() -> None:
    source = Path("abraxas/runes/operators/calibration.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("abraxas.forecast")
                assert "forecast_score" not in alias.name
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not module.startswith("abraxas.forecast")
            assert "forecast_score" not in module
    assert not Path("abraxas/runes/operators/forecast_score.py").exists()
    assert "RUNE.FORECAST_SCORE" in DECLARED_DEPENDENCIES
    assert implements_forecast_score() is False


def test_contract_object_is_shadow_validate_none() -> None:
    contract = get_abx_rune_contract("RUNE.CALIBRATION")
    assert contract.rune_id == "RUNE.CALIBRATION"
    assert "[" not in contract.rune_id
    assert "http://" not in contract.rune_id
    assert contract.acronym == "CAL"
    assert contract.version == "v0.1.0"
    assert contract.lane == "SHADOW"
    assert contract.category == "VALIDATE"
    assert contract.influence_policy == "NONE"
    assert [item.name for item in contract.inputs] == [
        "forecastLifecycles",
        "forecastScores",
        "horizonSpec",
    ]
    assert [item.name for item in contract.outputs] == [
        "calibrationReport",
        "performanceDrift",
        "horizonMetrics",
    ]
    assert "metric_not_computable" in contract.failure_modes
    assert "missing_resolution_data" in contract.failure_modes
    assert "horizon_mismatch" in contract.failure_modes
    assert "RUNE.FORECAST_SCORE" not in contract.dependencies
    assert "RUNE.CONTINUITY" not in contract.dependencies
    assert "RUNE.ERS" not in contract.dependencies
    policy = enforce_lane_policy(
        lane=contract.lane,
        influence_policy=contract.influence_policy,
        influences_active_path=False,
    )
    assert policy.status == "VALID"


def test_registry_binding_cites_plain_rune_id() -> None:
    binding = describe_rune("RUNE.CALIBRATION")
    assert binding.rune_id == "RUNE.CALIBRATION"
    assert binding.short_name == "CAL"
    assert binding.operator_path == "abraxas.runes.operators.calibration:apply_calibration"
    assert binding.version == "v0.1.0"


def test_apply_adapter_matches_calibrate() -> None:
    typed = _calibrate(seed=3, run_id="CALIBRATION-ADAPTER")
    dumped = apply_calibration(
        forecastLifecycles=_LIFECYCLES,
        forecastScores=_SCORES,
        horizonSpec=_HORIZON,
        seed=3,
        run_id="CALIBRATION-ADAPTER",
    )
    assert dumped == typed.model_dump()
    assert dumped["lane"] == "SHADOW"
    assert dumped["influence_policy"] == "NONE"
    assert dumped["category"] == "VALIDATE"
    assert dumped["live_scoring_activated"] is False
    assert dumped["calibration_incidents"] is None
    assert dumped["calibration_report"]["score"] is None
    assert dumped["calibration_report"]["incidents"] is None
    assert isinstance(typed, CalibrationResult)
