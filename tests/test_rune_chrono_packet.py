"""Goldens A/B/E (+ F) for RUNE.CHRONO_PACKET Shadow bind."""

from __future__ import annotations

from copy import deepcopy

from abraxas.runes.operators.chrono_align import align
from abraxas.runes.operators.chrono_overlay import overlay
from abraxas.runes.operators.chrono_packet import (
    FORBIDDEN_OBSERVED_KEYS,
    PACKET_LANE_VALUES,
    PACKET_STATUS_VALUES,
    PACKET_TOP_LEVEL_KEYS,
    PACKET_TYPE,
    ChronoPacketResult,
    apply_chrono_packet,
    compose,
)
from abraxas.runes.operators.chrono_scan import scan
from abraxas.runes.registry import describe_rune
from abx.lifecycle_policy import enforce_lane_policy
from abx.rune_contracts import get_abx_rune_contract

RUNE_ID = "RUNE.CHRONO_PACKET"

_STRONG_OBSERVED = {
    "cadence_interval": 600.0,
    "recurrence_strength": 1.0,
    "window_density": 0.001667,
    "timing_volatility": 0.0,
    "cadence_stability": 1.0,
    "recurrence_pressure": 1.0,
}
_STRONG_INFERRED = {
    "alignment_window": "next_cycle[600s]",
    "execution_readiness": "shadow_candidate",
    "timing_advantage_hypothesis": "bounded next-cycle[600s]; shadow-only; no outcome certainty",
    "window_decay_rate": 0.0,
}
_STRONG_SPECULATIVE = {
    "symbolic_time_markers": ["2026-04-16T09:00:00Z", "new_moon"],
    "ritual_timing_notes": ["symbolic reinforcement present but not used in forecast weighting"],
}
_PROVENANCE = {
    "source_family": ["chrono.fixture"],
    "source_ids": ["src-a"],
    "computation_path": ["RUNE.CHRONO_SCAN", "RUNE.CHRONO_ALIGN", "RUNE.CHRONO_OVERLAY"],
    "confidence": 0.71,
    "generated_at": "2026-04-15T11:00:00Z",
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
_SYMBOLS = [
    "new moon cluster around 2026-04-16T09:00:00Z",
    "marker:anniversary_window",
]
_NOTES = [
    "symbolic reinforcement present but not used in forecast weighting",
    "operator ritual note: keep overlay fenced",
]
_NULL_OBSERVED = {
    "cadence_interval": None,
    "recurrence_strength": None,
    "window_density": None,
    "timing_volatility": None,
    "cadence_stability": None,
    "recurrence_pressure": None,
}


def _compose(**kwargs):
    return compose(
        kwargs.pop("observed", _STRONG_OBSERVED),
        inferred=kwargs.pop("inferred", _STRONG_INFERRED),
        speculative=kwargs.pop("speculative", _STRONG_SPECULATIVE),
        provenance=kwargs.pop("provenance", _PROVENANCE),
        **kwargs,
    )


def _packet(result):
    return result.temporal_alignment_packet


def test_golden_a_determinism_identical_payloads() -> None:
    first = _compose(seed=7, run_id="CHRONO-PACKET-A")
    second = _compose(seed=7, run_id="CHRONO-PACKET-A")
    assert first.rune_id == RUNE_ID
    assert first.model_dump() == second.model_dump()
    packet = _packet(first)
    assert packet.packet_type == PACKET_TYPE
    assert packet.packet_version == "1.0.0"
    assert packet.lane == "SHADOW"
    assert packet.status == "active"
    assert packet.observed.model_dump() == _STRONG_OBSERVED
    assert packet.inferred.alignment_window is not None
    assert packet.inferred.alignment_window.window_label == "next_cycle[600s]"
    assert packet.inferred.alignment_window.start is None
    assert packet.inferred.alignment_window.end is None
    assert packet.inferred.execution_readiness is None
    assert packet.inferred.timing_advantage_hypothesis == _STRONG_INFERRED["timing_advantage_hypothesis"]
    assert packet.inferred.window_decay_rate == 0.0
    assert packet.speculative.model_dump() == _STRONG_SPECULATIVE
    assert first.provenance.input_hash == second.provenance.input_hash
    assert first.provenance.output_hash == second.provenance.output_hash
    assert first.lane == "SHADOW"
    assert first.influence_policy == "NONE"


def test_golden_a_seed_does_not_mutate_packet() -> None:
    left = _compose(seed=1)
    right = _compose(seed=99)
    assert _packet(left).model_dump() == _packet(right).model_dump()
    assert left.provenance.input_hash != right.provenance.input_hash


def test_golden_a_input_ordering_is_part_of_identity() -> None:
    left = compose(
        _STRONG_OBSERVED,
        inferred=_STRONG_INFERRED,
        speculative={
            "symbolic_time_markers": ["new_moon", "solstice"],
            "ritual_timing_notes": ["a", "b"],
        },
        provenance=_PROVENANCE,
    )
    right = compose(
        _STRONG_OBSERVED,
        inferred=_STRONG_INFERRED,
        speculative={
            "symbolic_time_markers": ["solstice", "new_moon"],
            "ritual_timing_notes": ["b", "a"],
        },
        provenance=_PROVENANCE,
    )
    assert _packet(left).speculative.symbolic_time_markers != _packet(right).speculative.symbolic_time_markers
    assert _packet(left).speculative.ritual_timing_notes != _packet(right).speculative.ritual_timing_notes


def test_golden_b_null_discipline_missing_blocks() -> None:
    result = compose(None, inferred=None, speculative=None, provenance=_PROVENANCE)
    packet = _packet(result)
    assert packet.status == "not_computable"
    assert packet.observed.model_dump() == _NULL_OBSERVED
    assert packet.inferred.alignment_window is None
    assert packet.inferred.execution_readiness is None
    assert packet.inferred.timing_advantage_hypothesis is None
    assert packet.inferred.window_decay_rate is None
    assert packet.speculative.symbolic_time_markers == []
    assert packet.speculative.ritual_timing_notes == []
    assert result.provenance.confidence is None


def test_golden_b_null_discipline_missing_provenance() -> None:
    result = compose(
        _STRONG_OBSERVED,
        inferred=_STRONG_INFERRED,
        speculative=_STRONG_SPECULATIVE,
        provenance=None,
    )
    packet = _packet(result)
    assert packet.status == "not_computable"
    assert packet.observed.model_dump() == _NULL_OBSERVED
    assert packet.speculative.symbolic_time_markers == []
    assert packet.inferred.alignment_window is None


def test_golden_b_null_discipline_incoming_not_computable() -> None:
    result = compose(
        {
            **_NULL_OBSERVED,
            "not_computable_flags": ["NOT_COMPUTABLE", "event_density_too_weak"],
        },
        inferred={
            "alignment_window": None,
            "execution_readiness": None,
            "timing_advantage_hypothesis": None,
            "window_decay_rate": None,
            "not_computable_flags": ["NOT_COMPUTABLE", "metrics_not_computable"],
        },
        speculative={"symbolic_time_markers": [], "ritual_timing_notes": []},
        provenance=_PROVENANCE,
    )
    packet = _packet(result)
    assert packet.status == "not_computable"
    assert packet.observed.cadence_interval is None
    assert packet.inferred.alignment_window is None
    assert packet.speculative.symbolic_time_markers == []
    assert result.provenance.confidence is None


def test_golden_b_does_not_fabricate_from_speculative() -> None:
    result = compose(
        None,
        inferred=None,
        speculative={
            "symbolic_time_markers": ["full_moon", "2026-09-04"],
            "ritual_timing_notes": ["symbolic date note without temporal events"],
            "cadence_interval": 3.0,
            "recurrence_strength": 0.99,
        },
        provenance=_PROVENANCE,
    )
    packet = _packet(result)
    assert packet.status == "not_computable"
    assert packet.observed.model_dump() == _NULL_OBSERVED
    assert packet.inferred.alignment_window is None
    assert packet.inferred.execution_readiness is None
    assert "full_moon" in packet.speculative.symbolic_time_markers
    assert "2026-09-04" in packet.speculative.symbolic_time_markers


def test_golden_e_packet_schema_required_fields() -> None:
    packet = _packet(_compose(run_id="CHRONO-PACKET-E"))
    dumped = packet.model_dump()
    assert set(dumped) == set(PACKET_TOP_LEVEL_KEYS)
    assert dumped["packet_type"] == "TemporalAlignmentPacket.v1"
    assert dumped["packet_version"] == "1.0.0"
    assert dumped["lane"] in PACKET_LANE_VALUES
    assert dumped["status"] in PACKET_STATUS_VALUES
    assert set(dumped["observed"]) == {
        "cadence_interval",
        "recurrence_strength",
        "window_density",
        "timing_volatility",
        "cadence_stability",
        "recurrence_pressure",
    }
    assert set(dumped["inferred"]) == {
        "alignment_window",
        "execution_readiness",
        "timing_advantage_hypothesis",
        "window_decay_rate",
    }
    assert set(dumped["speculative"]) == {
        "symbolic_time_markers",
        "ritual_timing_notes",
    }
    assert set(dumped["provenance"]) == {
        "source_family",
        "source_ids",
        "computation_path",
        "confidence",
        "generated_at",
    }
    assert dumped["lane"] == "SHADOW"
    assert "FORECAST" not in dumped.values()


def test_golden_e_missing_provenance_is_schema_failure() -> None:
    packet = _packet(compose(_STRONG_OBSERVED, provenance="not-a-record"))
    assert packet.status == "not_computable"
    assert packet.observed.model_dump() == _NULL_OBSERVED
    assert packet.provenance.computation_path == [RUNE_ID]


def test_golden_e_schema_noncompliance_wipes_unclean_blocks() -> None:
    packet = _packet(
        compose(
            {"cadence_interval": "fast"},
            inferred=_STRONG_INFERRED,
            speculative=_STRONG_SPECULATIVE,
            provenance=_PROVENANCE,
        )
    )
    assert packet.status == "not_computable"
    assert packet.observed.model_dump() == _NULL_OBSERVED
    assert packet.speculative.symbolic_time_markers == []
    assert packet.inferred.alignment_window is None


def test_golden_e_speculative_cannot_enter_observed() -> None:
    packet = _packet(
        compose(
            {
                **_STRONG_OBSERVED,
                "symbolic_time_markers": ["do-not-lift"],
                "ritual_timing_notes": ["also-do-not-lift"],
            },
            inferred=_STRONG_INFERRED,
            speculative={
                "symbolic_time_markers": ["new_moon"],
                "ritual_timing_notes": ["fenced"],
                "cadence_interval": 99.0,
                "execution_readiness": 0.99,
            },
            provenance=_PROVENANCE,
        )
    )
    observed = packet.observed.model_dump()
    for key in FORBIDDEN_OBSERVED_KEYS:
        assert key not in observed
    assert observed["cadence_interval"] == 600.0
    assert packet.speculative.symbolic_time_markers == ["new_moon"]
    assert packet.speculative.ritual_timing_notes == ["fenced"]
    assert "do-not-lift" not in packet.speculative.symbolic_time_markers
    assert packet.inferred.execution_readiness is None


def test_golden_e_does_not_promote_lane() -> None:
    packet = _packet(
        compose(
            _STRONG_OBSERVED,
            inferred=_STRONG_INFERRED,
            speculative=_STRONG_SPECULATIVE,
            provenance={**_PROVENANCE, "lane": "FORECAST"},
        )
    )
    assert packet.lane == "SHADOW"
    assert packet.status == "active"


def test_golden_f_chain_invariance() -> None:
    first = _chain(seed=7, run_id="CHRONO-PACKET-F")
    second = _chain(seed=7, run_id="CHRONO-PACKET-F")
    assert first.model_dump() == second.model_dump()
    packet = _packet(first)
    scanned, aligned, overlaid = _chain_parts()
    assert packet.observed.model_dump() == {
        key: getattr(scanned.observed, key) for key in _STRONG_OBSERVED
    }
    assert packet.inferred.alignment_window is not None
    assert packet.inferred.alignment_window.window_label == aligned.inferred.alignment_window
    assert packet.inferred.execution_readiness is None
    assert packet.inferred.timing_advantage_hypothesis == aligned.inferred.timing_advantage_hypothesis
    assert packet.speculative.symbolic_time_markers == overlaid.speculative.symbolic_time_markers
    assert packet.speculative.ritual_timing_notes == overlaid.speculative.ritual_timing_notes
    assert packet.provenance.computation_path == [
        "RUNE.CHRONO_SCAN",
        "RUNE.CHRONO_ALIGN",
        "RUNE.CHRONO_OVERLAY",
        RUNE_ID,
    ]
    for marker in packet.speculative.symbolic_time_markers:
        assert marker not in str(packet.observed.model_dump())
        assert marker not in str(packet.inferred.model_dump())


def test_golden_f_overlay_does_not_mutate_scan_align() -> None:
    scanned, aligned, overlaid = _chain_parts()
    observed_before = deepcopy(scanned.observed.model_dump())
    inferred_before = deepcopy(aligned.inferred.model_dump())
    result = compose(
        scanned,
        inferred=aligned,
        speculative=overlaid,
        provenance={
            "source_family": scanned.provenance.source_family_trace,
            "source_ids": scanned.provenance.source_ids,
            "computation_path": [scanned.rune_id, aligned.rune_id, overlaid.rune_id],
            "confidence": scanned.provenance.confidence,
            "generated_at": None,
        },
        run_id="CHRONO-PACKET-F",
        seed=7,
    )
    assert scanned.observed.model_dump() == observed_before
    assert aligned.inferred.model_dump() == inferred_before
    assert "observed" not in overlaid.model_dump()
    packet = _packet(result)
    assert packet.lane == "SHADOW"
    assert packet.observed.cadence_interval == observed_before["cadence_interval"]
    assert packet.status == "active"


def test_golden_f_vector_c_symbolic_only_stays_shadow() -> None:
    scanned = scan(None, source_family=["chrono.fixture"], time_field="timestamp")
    aligned = align(scanned)
    overlaid = overlay(
        ["full moon 2026-09-04"],
        operator_notes=["symbolic date note without temporal events"],
    )
    result = compose(
        scanned,
        inferred=aligned,
        speculative=overlaid,
        provenance={
            "source_family": ["operator_input"],
            "source_ids": [],
            "computation_path": [scanned.rune_id, aligned.rune_id, overlaid.rune_id],
            "confidence": None,
            "generated_at": None,
        },
    )
    packet = _packet(result)
    assert packet.status == "not_computable"
    assert packet.observed.model_dump() == _NULL_OBSERVED
    assert packet.inferred.alignment_window is None
    assert packet.inferred.execution_readiness is None
    assert "2026-09-04" in packet.speculative.symbolic_time_markers
    assert "full_moon" in packet.speculative.symbolic_time_markers
    assert packet.lane == "SHADOW"


def _chain_parts():
    scanned = scan(
        _STRONG_EVENTS,
        source_family=["chrono.fixture"],
        source_ids=["src-a"],
        time_field="timestamp",
        seed=7,
        run_id="CHRONO-PACKET-F",
    )
    aligned = align(scanned.observed, run_id="CHRONO-PACKET-F")
    overlaid = overlay(
        _SYMBOLS,
        operator_notes=_NOTES,
        temporal_context={
            "observed": scanned.observed.model_dump(),
            "inferred": aligned.inferred.model_dump(),
        },
        run_id="CHRONO-PACKET-F",
        seed=7,
    )
    return scanned, aligned, overlaid


def _chain(*, seed, run_id):
    scanned, aligned, overlaid = _chain_parts()
    return compose(
        scanned,
        inferred=aligned,
        speculative=overlaid,
        provenance={
            "source_family": scanned.provenance.source_family_trace,
            "source_ids": scanned.provenance.source_ids,
            "computation_path": [scanned.rune_id, aligned.rune_id, overlaid.rune_id],
            "confidence": scanned.provenance.confidence,
            "generated_at": None,
        },
        seed=seed,
        run_id=run_id,
    )


def test_no_wall_clock_without_caller_timestamp() -> None:
    packet = _packet(_compose(timestamp=None, provenance={**_PROVENANCE, "generated_at": None}))
    assert packet.provenance.generated_at is None


def test_contract_object_is_shadow_artifact_none() -> None:
    contract = get_abx_rune_contract(RUNE_ID)
    assert contract.rune_id == RUNE_ID
    assert contract.acronym == "CHP"
    assert contract.version == "v0.1.0"
    assert contract.lane == "SHADOW"
    assert contract.category == "ARTIFACT"
    assert contract.influence_policy == "NONE"
    assert [item.name for item in contract.inputs] == [
        "observed",
        "inferred",
        "speculative",
        "provenance",
    ]
    assert [item.name for item in contract.outputs] == ["temporalAlignmentPacket"]
    assert "not_computable" in contract.failure_modes
    assert "schema_noncompliance" in contract.failure_modes
    assert "missing_required_provenance" in contract.failure_modes
    assert "RUNE.CHRONO_SCAN" in contract.dependencies
    assert "RUNE.CHRONO_ALIGN" in contract.dependencies
    assert "RUNE.CHRONO_OVERLAY" in contract.dependencies
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
    assert binding.short_name == "CHP"
    assert binding.operator_path == "abraxas.runes.operators.chrono_packet:apply_chrono_packet"
    assert binding.version == "v0.1.0"


def test_apply_adapter_matches_compose() -> None:
    typed = _compose(seed=3, run_id="CHRONO-PACKET-ADAPTER")
    dumped = apply_chrono_packet(
        observed=_STRONG_OBSERVED,
        inferred=_STRONG_INFERRED,
        speculative=_STRONG_SPECULATIVE,
        provenance=_PROVENANCE,
        seed=3,
        run_id="CHRONO-PACKET-ADAPTER",
    )
    assert dumped == typed.model_dump()
    assert dumped["lane"] == "SHADOW"
    assert dumped["influence_policy"] == "NONE"
    assert dumped["temporal_alignment_packet"]["packet_type"] == PACKET_TYPE
    assert isinstance(typed, ChronoPacketResult)
