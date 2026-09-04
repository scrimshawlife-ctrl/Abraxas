"""Goldens A/B for RUNE.TRUST Shadow typed stub."""

from __future__ import annotations

from abraxas.runes.operators.trust import (
    DISTINCT_FROM,
    RUNE_ID,
    TrustResult,
    apply_trust,
    assess,
)
from abraxas.runes.registry import describe_rune
from abx.lifecycle_policy import enforce_lane_policy
from abx.rune_contracts import get_abx_rune_contract

_ORDERED_EVENTS = [
    {"id": "te-1", "kind": "attestation"},
    {"id": "te-2", "kind": "attestation"},
    {"id": "te-3", "kind": "attestation"},
]
_PRIOR = {"id": "state-0", "epoch": "2026-01-01T00:00:00Z"}
_OUTCOME_LINKS = [{"id": "ol-1", "forecast_id": None}]


def _assess(events=None, prior=None, **kwargs):
    if events is None:
        events = list(_ORDERED_EVENTS)
    if prior is None:
        prior = dict(_PRIOR)
    if "outcome_links" not in kwargs:
        kwargs["outcome_links"] = list(_OUTCOME_LINKS)
    return assess(events, prior, **kwargs)


def test_golden_a_determinism_identical_payloads() -> None:
    first = _assess(seed=7, run_id="TRUST-A")
    second = _assess(seed=7, run_id="TRUST-A")
    assert first.rune_id == "RUNE.TRUST"
    assert first.rune_id == RUNE_ID
    assert first.model_dump() == second.model_dump()
    assert first.provenance.input_hash == second.provenance.input_hash
    assert first.provenance.output_hash == second.provenance.output_hash
    assert first.lane == "SHADOW"
    assert first.influence_policy == "NONE"
    assert first.trust_assessment.score is None
    assert first.trust_state.score is None
    assert first.trust_update.delta is None
    assert first.trust_assessment.status == "NOT_COMPUTABLE"
    assert first.trust_state.status == "NOT_COMPUTABLE"
    assert first.trust_update.status == "NOT_COMPUTABLE"
    assert "NOT_COMPUTABLE" in first.trust_assessment.not_computable_flags
    assert "trust_not_computable" in first.trust_assessment.not_computable_flags
    assert first.provenance.confidence is None


def test_golden_a_event_order_is_part_of_identity() -> None:
    left = _assess(_ORDERED_EVENTS)
    right = _assess(list(reversed(_ORDERED_EVENTS)))
    assert left.provenance.input_hash != right.provenance.input_hash
    assert left.trust_assessment.score is None
    assert right.trust_assessment.score is None


def test_golden_a_seed_does_not_invent_scores() -> None:
    left = _assess(seed=1)
    right = _assess(seed=99)
    assert left.trust_assessment.model_dump() == right.trust_assessment.model_dump()
    assert left.trust_state.model_dump() == right.trust_state.model_dump()
    assert left.trust_update.model_dump() == right.trust_update.model_dump()
    assert left.provenance.input_hash != right.provenance.input_hash


def test_golden_b_null_discipline_missing_inputs() -> None:
    missing_events = assess(None, _PRIOR, outcome_links=_OUTCOME_LINKS)
    missing_prior = assess(_ORDERED_EVENTS, None, outcome_links=_OUTCOME_LINKS)
    for result in (missing_events, missing_prior):
        assert result.trust_assessment.score is None
        assert result.trust_state.score is None
        assert result.trust_update.delta is None
        assert result.trust_assessment.status == "NOT_COMPUTABLE"
        assert "NOT_COMPUTABLE" in result.trust_assessment.not_computable_flags
        assert "trust_not_computable" in result.trust_assessment.not_computable_flags
        assert result.provenance.confidence is None


def test_golden_b_null_discipline_weak_placeholder() -> None:
    result = assess(
        [{"status": "NOT_COMPUTABLE"}, {"placeholder": True}],
        {"status": "NOT_COMPUTABLE"},
        outcome_links=None,
    )
    assert result.trust_assessment.score is None
    assert result.trust_state.score is None
    assert result.trust_update.delta is None
    flags = result.trust_assessment.not_computable_flags
    assert "NOT_COMPUTABLE" in flags
    assert "trust_not_computable" in flags
    assert "placeholder_or_weak_input" in flags
    assert "missing_outcome_mapping" in flags


def test_golden_b_empty_and_unparseable() -> None:
    empty = assess([], {}, outcome_links=[])
    junk = assess("not-events", "not-state", outcome_links="not-links")
    for result in (empty, junk):
        assert result.trust_assessment.score is None
        assert result.trust_state.score is None
        assert "NOT_COMPUTABLE" in result.trust_assessment.not_computable_flags
        assert "trust_not_computable" in result.trust_assessment.not_computable_flags


def test_no_wall_clock_without_caller_timestamp() -> None:
    result = _assess(timestamp=None)
    assert result.provenance.timestamp is None


def test_contract_object_is_shadow_detect_none() -> None:
    contract = get_abx_rune_contract("RUNE.TRUST")
    assert contract.rune_id == "RUNE.TRUST"
    assert contract.rune_id != "RUNE.TRUST_CUE_SCAN"
    assert contract.rune_id != DISTINCT_FROM
    assert "[" not in contract.rune_id
    assert "http://" not in contract.rune_id
    assert contract.acronym == "TRU"
    assert contract.version == "v0.1.0"
    assert contract.lane == "SHADOW"
    assert contract.category == "DETECT"
    assert contract.influence_policy == "NONE"
    assert [item.name for item in contract.inputs] == [
        "trustEvents",
        "priorTrustState",
        "outcomeLinks",
    ]
    assert [item.name for item in contract.outputs] == [
        "trustAssessment",
        "trustState",
        "trustUpdate",
    ]
    assert "trust_not_computable" in contract.failure_modes
    assert "missing_outcome_mapping" in contract.failure_modes
    assert "contradiction_overload" in contract.failure_modes
    assert "RUNE.FORECAST_SCORE" not in contract.dependencies
    assert "RUNE.DRIFT" not in contract.dependencies
    assert "RUNE.ERS" not in contract.dependencies
    assert "RUNE.CONTINUITY" not in contract.dependencies
    policy = enforce_lane_policy(
        lane=contract.lane,
        influence_policy=contract.influence_policy,
        influences_active_path=False,
    )
    assert policy.status == "VALID"


def test_registry_binding_cites_plain_rune_id() -> None:
    binding = describe_rune("RUNE.TRUST")
    assert binding.rune_id == "RUNE.TRUST"
    assert binding.rune_id != "RUNE.TRUST_CUE_SCAN"
    assert binding.short_name == "TRU"
    assert binding.operator_path == "abraxas.runes.operators.trust:apply_trust"
    assert binding.version == "v0.1.0"


def test_apply_adapter_matches_assess() -> None:
    typed = _assess(seed=3, run_id="TRUST-ADAPTER")
    dumped = apply_trust(
        trustEvents=_ORDERED_EVENTS,
        priorTrustState=_PRIOR,
        outcomeLinks=_OUTCOME_LINKS,
        seed=3,
        run_id="TRUST-ADAPTER",
    )
    assert dumped == typed.model_dump()
    assert dumped["lane"] == "SHADOW"
    assert dumped["influence_policy"] == "NONE"
    assert dumped["trust_assessment"]["score"] is None
    assert isinstance(typed, TrustResult)
