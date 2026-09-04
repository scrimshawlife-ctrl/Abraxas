"""Goldens A/B/D for RUNE.CHRONO_OVERLAY Shadow bind."""

from __future__ import annotations

from copy import deepcopy

from abraxas.runes.operators.chrono_align import align
from abraxas.runes.operators.chrono_overlay import (
    FORBIDDEN_EVIDENCE_KEYS,
    ChronoOverlayResult,
    apply_chrono_overlay,
    overlay,
)
from abraxas.runes.operators.chrono_scan import scan
from abraxas.runes.registry import describe_rune
from abx.lifecycle_policy import enforce_lane_policy
from abx.rune_contracts import get_abx_rune_contract

RUNE_ID = "RUNE.CHRONO_OVERLAY"

_SYMBOLS = [
    "new moon cluster around 2026-04-16T09:00:00Z",
    "marker:anniversary_window",
]
_NOTES = [
    "symbolic reinforcement present but not used in forecast weighting",
    "operator ritual note: keep overlay fenced",
]
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


def _overlay(**kwargs):
    return overlay(
        kwargs.pop("symbolic_inputs", _SYMBOLS),
        operator_notes=kwargs.pop("operator_notes", _NOTES),
        **kwargs,
    )


def _scan_strong():
    return scan(
        _STRONG_EVENTS,
        source_family=["chrono.fixture"],
        source_ids=["src-a"],
        time_field="timestamp",
        seed=7,
        run_id="CHRONO-OVERLAY-CHAIN",
    )


def test_golden_a_determinism_identical_payloads() -> None:
    first = _overlay(seed=7, run_id="CHRONO-OVERLAY-A")
    second = _overlay(seed=7, run_id="CHRONO-OVERLAY-A")
    assert first.rune_id == RUNE_ID
    assert first.model_dump() == second.model_dump()
    assert first.speculative.symbolic_time_markers == [
        "2026-04-16T09:00:00Z",
        "marker:anniversary_window",
        "new_moon",
    ]
    assert first.speculative.ritual_timing_notes == _NOTES
    assert first.speculative.not_computable_flags == []
    assert first.provenance.confidence is not None
    assert first.provenance.confidence < 0.5
    assert first.provenance.input_hash == second.provenance.input_hash
    assert first.provenance.output_hash == second.provenance.output_hash
    assert first.lane == "SHADOW"
    assert first.influence_policy == "NONE"


def test_golden_a_seed_does_not_mutate_speculative() -> None:
    left = _overlay(seed=1)
    right = _overlay(seed=99)
    assert left.speculative.model_dump() == right.speculative.model_dump()
    assert left.provenance.input_hash != right.provenance.input_hash


def test_golden_a_input_ordering_is_part_of_identity() -> None:
    left = overlay(["new_moon", "solstice"], operator_notes=["a", "b"])
    right = overlay(["solstice", "new_moon"], operator_notes=["b", "a"])
    assert left.speculative.symbolic_time_markers != right.speculative.symbolic_time_markers
    assert left.speculative.ritual_timing_notes != right.speculative.ritual_timing_notes


def test_golden_b_null_discipline_missing_inputs() -> None:
    result = overlay(None)
    assert result.speculative.symbolic_time_markers == []
    assert result.speculative.ritual_timing_notes == []
    assert "NOT_COMPUTABLE" in result.speculative.not_computable_flags
    assert "symbolic_input_too_weak" in result.speculative.not_computable_flags
    assert result.provenance.confidence is None


def test_golden_b_null_discipline_empty_and_unparseable() -> None:
    empty = overlay([], operator_notes=[])
    junk = overlay("not-a-list", operator_notes="also-not-a-list")
    vague = overlay(["feels lucky today", "vibes only"], operator_notes=[])
    for result in (empty, junk, vague):
        assert result.speculative.symbolic_time_markers == []
        assert result.speculative.ritual_timing_notes == []
        assert "NOT_COMPUTABLE" in result.speculative.not_computable_flags
        assert "symbolic_input_too_weak" in result.speculative.not_computable_flags


def test_golden_b_invalid_temporal_context_fail_closed() -> None:
    result = overlay(_SYMBOLS, operator_notes=_NOTES, temporal_context="not-a-record")
    assert result.speculative.symbolic_time_markers == []
    assert result.speculative.ritual_timing_notes == []
    assert "not_computable" in result.speculative.not_computable_flags
    assert "NOT_COMPUTABLE" in result.speculative.not_computable_flags


def test_golden_c_weak_signal_does_not_improvise() -> None:
    result = overlay(["maybe later", "important feeling"], operator_notes=[])
    assert result.speculative.symbolic_time_markers == []
    assert result.speculative.ritual_timing_notes == []
    assert "symbolic_input_too_weak" in result.speculative.not_computable_flags
    assert result.provenance.confidence is None


def test_golden_d_speculative_stays_fenced() -> None:
    result = _overlay(run_id="CHRONO-OVERLAY-D")
    dumped = result.model_dump()
    assert "observed" not in dumped
    assert "inferred" not in dumped
    for key in FORBIDDEN_EVIDENCE_KEYS:
        assert key not in dumped
        assert key not in dumped["speculative"]
        assert key not in dumped["provenance"]
    assert set(dumped["speculative"]) == {
        "symbolic_time_markers",
        "ritual_timing_notes",
        "not_computable_flags",
    }


def test_golden_d_does_not_contaminate_scan_or_align() -> None:
    scanned = _scan_strong()
    aligned = align(scanned.observed, run_id="CHRONO-OVERLAY-CHAIN")
    observed_before = deepcopy(scanned.observed.model_dump())
    inferred_before = deepcopy(aligned.inferred.model_dump())
    context = {
        "observed": deepcopy(observed_before),
        "inferred": deepcopy(inferred_before),
        "execution_readiness": aligned.inferred.execution_readiness,
    }

    result = overlay(
        _SYMBOLS,
        operator_notes=_NOTES,
        temporal_context=context,
        run_id="CHRONO-OVERLAY-CHAIN",
    )

    assert result.speculative.symbolic_time_markers
    assert result.speculative.ritual_timing_notes == _NOTES
    assert "observed" not in result.model_dump()
    assert "inferred" not in result.model_dump()
    assert getattr(result, "observed", None) is None
    assert getattr(result, "inferred", None) is None

    scanned_after = _scan_strong()
    aligned_after = align(scanned_after.observed, run_id="CHRONO-OVERLAY-CHAIN")
    assert scanned_after.observed.model_dump() == observed_before
    assert aligned_after.inferred.model_dump() == inferred_before
    assert context["observed"] == observed_before
    assert context["inferred"] == inferred_before
    assert context["execution_readiness"] == "shadow_candidate"
    assert aligned_after.inferred.execution_readiness == "shadow_candidate"
    assert aligned_after.inferred.alignment_window == "next_cycle[600s]"
    for marker in result.speculative.symbolic_time_markers:
        assert marker not in str(scanned_after.observed.model_dump())
        assert marker not in str(aligned_after.inferred.model_dump())


def test_golden_d_vector_c_symbolic_only_leaves_scan_align_null() -> None:
    scanned = scan(None, source_family=["chrono.fixture"], time_field="timestamp")
    aligned = align(scanned)
    result = overlay(
        ["full moon 2026-09-04"],
        operator_notes=["symbolic date note without temporal events"],
        temporal_context={
            "observed": scanned.observed.model_dump(),
            "inferred": aligned.inferred.model_dump(),
        },
    )
    assert "2026-09-04" in result.speculative.symbolic_time_markers
    assert "full_moon" in result.speculative.symbolic_time_markers
    assert result.speculative.ritual_timing_notes == [
        "symbolic date note without temporal events"
    ]
    assert scanned.observed.cadence_interval is None
    assert scanned.observed.recurrence_strength is None
    assert "NOT_COMPUTABLE" in scanned.observed.not_computable_flags
    assert aligned.inferred.alignment_window is None
    assert aligned.inferred.execution_readiness is None
    assert aligned.inferred.timing_advantage_hypothesis is None
    assert "NOT_COMPUTABLE" in aligned.inferred.not_computable_flags


def test_temporal_context_does_not_mint_markers() -> None:
    context = {
        "observed": {"cadence_interval": 600.0},
        "symbolic_inputs": ["new_moon 2026-01-01"],
        "operator_notes": ["do not lift this"],
    }
    result = overlay(["feels lucky"], operator_notes=[], temporal_context=context)
    assert result.speculative.symbolic_time_markers == []
    assert result.speculative.ritual_timing_notes == []
    assert "symbolic_input_too_weak" in result.speculative.not_computable_flags


def test_contract_object_is_shadow_explain_none() -> None:
    contract = get_abx_rune_contract(RUNE_ID)
    assert contract.rune_id == RUNE_ID
    assert contract.acronym == "CHO"
    assert contract.version == "v0.1.0"
    assert contract.lane == "SHADOW"
    assert contract.category == "EXPLAIN"
    assert contract.influence_policy == "NONE"
    assert [item.name for item in contract.inputs] == [
        "symbolic_inputs",
        "operator_notes",
        "temporal_context",
    ]
    assert [item.name for item in contract.outputs] == ["speculative", "provenance"]
    assert "not_computable" in contract.failure_modes
    assert "symbolic_input_too_weak" in contract.failure_modes
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
    assert binding.short_name == "CHO"
    assert binding.operator_path == "abraxas.runes.operators.chrono_overlay:apply_chrono_overlay"
    assert binding.version == "v0.1.0"


def test_apply_adapter_matches_overlay() -> None:
    typed = _overlay(seed=3, run_id="CHRONO-OVERLAY-ADAPTER")
    dumped = apply_chrono_overlay(
        symbolic_inputs=_SYMBOLS,
        operator_notes=_NOTES,
        seed=3,
        run_id="CHRONO-OVERLAY-ADAPTER",
    )
    assert dumped == typed.model_dump()
    assert dumped["lane"] == "SHADOW"
    assert dumped["influence_policy"] == "NONE"
    assert isinstance(typed, ChronoOverlayResult)
