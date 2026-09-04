"""Goldens A/B (+ C) for RUNE.CHRONO_ALIGN Shadow bind."""

from __future__ import annotations

from abraxas.runes.operators.chrono_align import ChronoAlignResult, align, apply_chrono_align
from abraxas.runes.operators.chrono_scan import scan
from abraxas.runes.registry import describe_rune
from abx.lifecycle_policy import enforce_lane_policy
from abx.rune_contracts import get_abx_rune_contract

RUNE_ID = "RUNE.CHRONO_ALIGN"

_STRONG_METRICS = {
    "cadence_interval": 600.0,
    "recurrence_strength": 1.0,
    "window_density": 0.001667,
    "timing_volatility": 0.0,
    "cadence_stability": 1.0,
    "recurrence_pressure": 1.0,
}

_STRONG_EVENTS = [
    {"id": "e3", "timestamp": "2026-01-01T00:20:00Z"},
    {"id": "e1", "timestamp": "2026-01-01T00:00:00Z"},
    {"id": "e2", "timestamp": "2026-01-01T00:10:00Z"},
    {"id": "e4", "timestamp": "2026-01-01T00:30:00Z"},
    {"id": "e5", "timestamp": "2026-01-01T00:40:00Z"},
    {"id": "e6", "timestamp": "2026-01-01T00:50:00Z"},
    {"id": "e7", "timestamp": "2026-01-01T01:00:00Z"},
    {"id": "e8", "timestamp": "2026-01-01T01:10:00Z"},
]


def _align(metrics, **kwargs):
    return align(metrics, **kwargs)


def test_golden_a_determinism_identical_payloads() -> None:
    first = _align(
        _STRONG_METRICS,
        candidate_actions=["hold", "release"],
        alignment_policy={"min_confidence": 0.5, "max_window_span": "1h"},
        seed=7,
        run_id="CHRONO-ALIGN-A",
    )
    second = _align(
        _STRONG_METRICS,
        candidate_actions=["hold", "release"],
        alignment_policy={"min_confidence": 0.5, "max_window_span": "1h"},
        seed=7,
        run_id="CHRONO-ALIGN-A",
    )
    assert first.rune_id == RUNE_ID
    assert first.model_dump() == second.model_dump()
    assert first.inferred.alignment_window == "next_cycle[600s];candidates=hold|release"
    assert first.inferred.execution_readiness == "shadow_candidate"
    assert first.inferred.timing_advantage_hypothesis is not None
    assert "no outcome certainty" in first.inferred.timing_advantage_hypothesis
    assert first.inferred.window_decay_rate == 0.0
    assert first.inferred.not_computable_flags == []
    assert first.provenance.confidence is not None
    assert first.provenance.confidence >= 0.5
    assert first.provenance.input_hash == second.provenance.input_hash
    assert first.provenance.output_hash == second.provenance.output_hash


def test_golden_a_seed_does_not_mutate_inferred_windows() -> None:
    left = _align(_STRONG_METRICS, seed=1)
    right = _align(_STRONG_METRICS, seed=99)
    assert left.inferred.model_dump() == right.inferred.model_dump()
    assert left.provenance.input_hash != right.provenance.input_hash


def test_golden_a_candidate_actions_ordering_is_part_of_identity() -> None:
    left = _align(_STRONG_METRICS, candidate_actions=["hold", "release"])
    right = _align(_STRONG_METRICS, candidate_actions=["release", "hold"])
    assert left.inferred.alignment_window != right.inferred.alignment_window
    assert left.inferred.execution_readiness == right.inferred.execution_readiness


def test_golden_b_null_discipline_missing_metrics() -> None:
    result = _align(None)
    assert result.inferred.alignment_window is None
    assert result.inferred.execution_readiness is None
    assert result.inferred.timing_advantage_hypothesis is None
    assert result.inferred.window_decay_rate is None
    assert "NOT_COMPUTABLE" in result.inferred.not_computable_flags
    assert "metrics_not_computable" in result.inferred.not_computable_flags
    assert result.provenance.confidence is None


def test_golden_b_null_discipline_empty_and_unparseable() -> None:
    empty = _align({})
    junk = _align("not-metrics")
    for result in (empty, junk):
        assert result.inferred.alignment_window is None
        assert "NOT_COMPUTABLE" in result.inferred.not_computable_flags
        assert result.inferred.not_computable_flags


def test_golden_b_invalid_policy_fail_closed() -> None:
    result = _align(_STRONG_METRICS, alignment_policy={"max_window_span": "not-a-span"})
    assert result.inferred.alignment_window is None
    assert "policy_invalid" in result.inferred.not_computable_flags
    assert "NOT_COMPUTABLE" in result.inferred.not_computable_flags


def test_golden_b_scan_nulls_do_not_improvise_window() -> None:
    scan_null = scan(None, source_family=["chrono.fixture"], time_field="timestamp")
    result = _align(scan_null)
    assert result.inferred.alignment_window is None
    assert result.inferred.execution_readiness is None
    assert "metrics_not_computable" in result.inferred.not_computable_flags
    assert "NOT_COMPUTABLE" in result.inferred.not_computable_flags


def test_golden_c_weak_signal_does_not_escalate() -> None:
    weak = {
        "cadence_interval": 86400.0,
        "recurrence_strength": 0.22,
        "window_density": 0.01,
        "timing_volatility": 0.86,
        "cadence_stability": 0.14,
        "recurrence_pressure": 0.1,
    }
    result = _align(weak, candidate_actions=["force-window"])
    assert result.inferred.alignment_window is None
    assert result.inferred.execution_readiness is None
    assert result.inferred.timing_advantage_hypothesis is None
    assert "NOT_COMPUTABLE" in result.inferred.not_computable_flags
    assert "no_lawful_window" in result.inferred.not_computable_flags
    assert result.provenance.confidence is None


def test_contract_cited_policy_floor_and_span_fail_closed() -> None:
    mid = {
        "cadence_interval": 600.0,
        "recurrence_strength": 0.9,
        "window_density": 0.001667,
        "timing_volatility": 0.1,
        "cadence_stability": 0.9,
        "recurrence_pressure": 0.8,
    }
    high_floor = _align(mid, alignment_policy={"min_confidence": 0.99})
    assert high_floor.inferred.alignment_window is None
    assert "no_lawful_window" in high_floor.inferred.not_computable_flags
    assert high_floor.inferred.execution_readiness is None

    over_span = _align(
        _STRONG_METRICS,
        alignment_policy={"min_confidence": 0.5, "max_window_span": "5m"},
    )
    assert over_span.inferred.alignment_window is None
    assert "no_lawful_window" in over_span.inferred.not_computable_flags


def test_contract_cited_scan_chain_vector_a() -> None:
    scanned = scan(
        _STRONG_EVENTS,
        source_family=["chrono.fixture"],
        source_ids=["src-a"],
        time_field="timestamp",
        seed=7,
        run_id="CHRONO-CHAIN",
    )
    result = _align(scanned.observed, run_id="CHRONO-CHAIN")
    assert scanned.observed.cadence_interval == 600.0
    assert scanned.observed.not_computable_flags == []
    assert result.inferred.alignment_window == "next_cycle[600s]"
    assert result.inferred.execution_readiness == "shadow_candidate"
    assert result.inferred.not_computable_flags == []
    assert result.lane == "SHADOW"
    assert result.influence_policy == "NONE"


def test_contract_object_is_shadow_schedule_none() -> None:
    contract = get_abx_rune_contract(RUNE_ID)
    assert contract.rune_id == RUNE_ID
    assert contract.acronym == "CHA"
    assert contract.version == "v0.1.0"
    assert contract.lane == "SHADOW"
    assert contract.category == "SCHEDULE"
    assert contract.influence_policy == "NONE"
    assert [item.name for item in contract.inputs] == [
        "observed_temporal_metrics",
        "candidate_actions",
        "alignment_policy",
    ]
    assert [item.name for item in contract.outputs] == ["inferred", "provenance"]
    assert "not_computable" in contract.failure_modes
    assert "metrics_not_computable" in contract.failure_modes
    assert "no_lawful_window" in contract.failure_modes
    assert "policy_invalid" in contract.failure_modes
    assert "RUNE.CHRONO_SCAN" in contract.dependencies
    assert "RUNE.ERS" not in contract.dependencies
    policy = enforce_lane_policy(
        lane=contract.lane,
        influence_policy=contract.influence_policy,
        influences_active_path=False,
    )
    assert policy.status == "VALID"


def test_registry_binding_cites_rune_id() -> None:
    binding = describe_rune(RUNE_ID)
    assert binding.rune_id == RUNE_ID
    assert binding.short_name == "CHA"
    assert binding.operator_path == "abraxas.runes.operators.chrono_align:apply_chrono_align"
    assert binding.version == "v0.1.0"


def test_apply_adapter_matches_align() -> None:
    typed = _align(_STRONG_METRICS, seed=3, run_id="CHRONO-ALIGN-ADAPTER")
    dumped = apply_chrono_align(
        observed_temporal_metrics=_STRONG_METRICS,
        seed=3,
        run_id="CHRONO-ALIGN-ADAPTER",
    )
    assert dumped == typed.model_dump()
    assert dumped["lane"] == "SHADOW"
    assert dumped["influence_policy"] == "NONE"
    assert isinstance(typed, ChronoAlignResult)
