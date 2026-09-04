"""Goldens A/B (+ C) for RUNE.CHRONO_SCAN Shadow bind."""

from __future__ import annotations

from abraxas.runes.operators.chrono_scan import ChronoScanResult, apply_chrono_scan, scan
from abraxas.runes.registry import describe_rune
from abx.lifecycle_policy import enforce_lane_policy
from abx.rune_contracts import get_abx_rune_contract

RUNE_ID = "RUNE.CHRONO_SCAN"

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


def _scan(events, **kwargs):
    return scan(
        events,
        source_family=["chrono.fixture"],
        source_ids=["src-a"],
        time_field="timestamp",
        **kwargs,
    )


def test_golden_a_determinism_identical_payloads() -> None:
    first = _scan(_STRONG_EVENTS, seed=7, run_id="CHRONO-A")
    second = _scan(_STRONG_EVENTS, seed=7, run_id="CHRONO-A")
    assert first.rune_id == RUNE_ID
    assert first.model_dump() == second.model_dump()
    assert first.observed.cadence_interval == 600.0
    assert first.observed.not_computable_flags == []
    assert first.observed.recurrence_strength is not None
    assert first.observed.recurrence_strength >= 0.9
    assert first.provenance.confidence is not None
    assert first.provenance.input_hash == second.provenance.input_hash
    assert first.provenance.output_hash == second.provenance.output_hash


def test_golden_a_seed_does_not_mutate_observed_metrics() -> None:
    left = _scan(_STRONG_EVENTS, seed=1)
    right = _scan(_STRONG_EVENTS, seed=99)
    assert left.observed.model_dump() == right.observed.model_dump()
    assert left.provenance.input_hash != right.provenance.input_hash


def test_golden_b_null_discipline_missing_events() -> None:
    result = _scan(None)
    assert result.observed.cadence_interval is None
    assert result.observed.recurrence_strength is None
    assert result.observed.window_density is None
    assert result.observed.timing_volatility is None
    assert result.observed.cadence_stability is None
    assert result.observed.recurrence_pressure is None
    assert "NOT_COMPUTABLE" in result.observed.not_computable_flags
    assert "timestamps_missing" in result.observed.not_computable_flags
    assert result.provenance.confidence is None


def test_golden_b_null_discipline_empty_and_unparseable() -> None:
    empty = _scan([])
    junk = _scan([{"id": "x", "note": "no time"}, "not-an-event"])
    for result in (empty, junk):
        assert result.observed.cadence_interval is None
        assert "NOT_COMPUTABLE" in result.observed.not_computable_flags
        assert result.observed.not_computable_flags


def test_golden_b_invalid_window_fail_closed() -> None:
    result = _scan(_STRONG_EVENTS, window_config={"lookback_span": "not-a-span"})
    assert result.observed.cadence_interval is None
    assert "window_config_invalid" in result.observed.not_computable_flags
    assert "NOT_COMPUTABLE" in result.observed.not_computable_flags


def test_golden_c_weak_signal_does_not_invent_cadence() -> None:
    weak = [
        {"timestamp": "2026-01-01T00:00:00Z"},
        {"timestamp": "2026-01-01T00:03:00Z"},
        {"timestamp": "2026-01-02T12:00:00Z"},
        {"timestamp": "2026-01-10T01:17:00Z"},
    ]
    result = _scan(weak)
    assert result.observed.cadence_interval is None
    assert result.observed.recurrence_strength is None
    assert result.observed.recurrence_pressure is None
    assert "NOT_COMPUTABLE" in result.observed.not_computable_flags
    assert result.provenance.confidence is None
    assert result.observed.timing_volatility is None or result.observed.timing_volatility > 0.75


def test_contract_object_is_shadow_detect_none() -> None:
    contract = get_abx_rune_contract(RUNE_ID)
    assert contract.rune_id == RUNE_ID
    assert contract.acronym == "CHS"
    assert contract.version == "v0.1.0"
    assert contract.lane == "SHADOW"
    assert contract.category == "DETECT"
    assert contract.influence_policy == "NONE"
    assert [item.name for item in contract.inputs] == [
        "source_family",
        "source_ids",
        "events",
        "time_field",
        "window_config",
    ]
    assert [item.name for item in contract.outputs] == ["observed", "provenance"]
    assert "not_computable" in contract.failure_modes
    assert "timestamps_missing" in contract.failure_modes
    policy = enforce_lane_policy(
        lane=contract.lane,
        influence_policy=contract.influence_policy,
        influences_active_path=False,
    )
    assert policy.status == "VALID"


def test_registry_binding_cites_rune_id() -> None:
    binding = describe_rune(RUNE_ID)
    assert binding.rune_id == RUNE_ID
    assert binding.short_name == "CHS"
    assert binding.operator_path == "abraxas.runes.operators.chrono_scan:apply_chrono_scan"
    assert binding.version == "v0.1.0"


def test_apply_adapter_matches_scan() -> None:
    typed = _scan(_STRONG_EVENTS, seed=3, run_id="CHRONO-ADAPTER")
    dumped = apply_chrono_scan(
        events=_STRONG_EVENTS,
        source_family=["chrono.fixture"],
        source_ids=["src-a"],
        time_field="timestamp",
        seed=3,
        run_id="CHRONO-ADAPTER",
    )
    assert dumped == typed.model_dump()
    assert dumped["lane"] == "SHADOW"
    assert dumped["influence_policy"] == "NONE"
    assert isinstance(typed, ChronoScanResult)
