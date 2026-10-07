"""Semion instrument tests.

Mirrors the contract of `abraxas/evidence/hyperlex_instrument.py` — the comparison point the engine
manifest itself names — because both engines are deliberate SHADOW surfaces whose output must never
acquire authority.

THE DEFECT THIS FILE EXISTS TO PREVENT

The engine manifest recorded that Semion's provider "exists only as a class INSIDE a test". That test
provider was a stub that IGNORED its claim and returned a hardcoded `answer="qualisign-rheme-icon"` at a
fixed `confidence=0.85`. Extracting that into a real module would have shipped a rubber stamp with a
confidence value attached — the exact failure the `planned` label was holding back.

So the tests below drive the three things a real instrument must do:

1. CARRY the frame's own classification rather than inventing one (it consumes; it does not classify);
2. REFUSE anything claiming authority — `semantic_truth`, `may_authorize`, `may_mutate_governing_state`
   are all true-or-refuse, and a forbidden kind is refused by name;
3. RECORD a failed classification instead of smoothing it into a confident answer.

Wire shapes come from `semion_sign_relation_v1.spec.md` § 3.1 and the fixtures in
`abraxas/evidence/semion_q1_fixtures.yaml`.
"""

from __future__ import annotations

import copy

import pytest

from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType
from abraxas.evidence.semion_instrument import (
    ALLOWED_KINDS,
    FEATURE_ENV,
    SemionAuthorityError,
    adapt_observation,
    assert_not_authoritative,
    instrument_enabled,
    promote_to_canonical_state,
    to_evidence_envelope,
)

#: The valid frame from semion_q1_fixtures.yaml (fixture_valid_qualisign_rheme_icon).
VALID_FRAME: dict = {
    "schema": "semion.sign.v1",
    "version": "SEMION_SIGN_RELATION_V1",
    "observation_id": "abc12345deadbeef",
    "input_hash": "0" * 64,
    "authority": {
        "kind": "advisory",
        "source": "semion",
        "semantic_truth": False,
        "may_authorize": False,
        "may_mutate_governing_state": False,
        "role": "OBSERVATION",
    },
    "sign_class": "qualisign-rheme-icon",
    "sign_class_valid": True,
    "sign_class_errors": [],
    "interpretant_coherence": 1.0,
    "representamen_object_alignment": 1.0,
    "relation_steps": [
        {
            "relation": "resembles",
            "subject": "sign_a",
            "object": "sign_b",
            "result": "similar",
            "confidence": 0.9,
            "metadata": {},
        }
    ],
    "peircean_analysis": {
        "existence": "qualisign",
        "thirdness": "rheme",
        "relation": "icon",
        "valid_combination": True,
        "coherence_score": 0.95,
    },
    "provenance": {
        "instrument_version": "SEMION_SIGN_RELATION_V1",
        "contract_version": "semion.sign.v1",
        "ontology_version": "PEIRCE_CATEGORIES_V1_FINAL",
        "manifest_sha256": "c" * 64,
        "schema_sha256": "d" * 64,
    },
}


def _frame(**overrides) -> dict:
    """A deep copy of the valid frame with the given top-level overrides applied."""
    frame = copy.deepcopy(VALID_FRAME)
    for key, value in overrides.items():
        if key == "authority":
            frame["authority"].update(value)
        else:
            frame[key] = value
    return frame


def test_the_instrument_is_disabled_by_default() -> None:
    """Feature-gated SHADOW integration: off unless explicitly enabled, like hyperlex."""
    import os

    assert os.environ.get(FEATURE_ENV) is None
    assert instrument_enabled() is False


def test_the_allowed_kinds_match_the_wire_contract() -> None:
    assert ALLOWED_KINDS == ("OBSERVATION", "EVIDENCE", "SHADOW_SIGNAL")
    for kind in ALLOWED_KINDS:
        adapt_observation(VALID_FRAME, kind=kind)


def test_a_valid_frame_adapts_to_advisory_shadow_evidence() -> None:
    evidence = adapt_observation(VALID_FRAME)
    assert evidence["lane"] == "shadow"
    assert evidence["influence_policy"] == "NONE"
    assert evidence["valid_for_forecast"] is False
    assert evidence["semantic_truth"] is False


def test_the_instrument_carries_the_frames_classification_and_invents_none() -> None:
    """It CONSUMES a classification. Semion's own docs: 'Semion does not import Abraxas. Abraxas may
    consume this dict.' An instrument that classified would be a second classifier."""
    evidence = adapt_observation(VALID_FRAME)
    assert evidence["sign_class"] == VALID_FRAME["sign_class"]
    assert evidence["peircean_analysis"] == VALID_FRAME["peircean_analysis"]

    other = _frame(sign_class="sinsign-dicent-index", peircean_analysis={
        "existence": "sinsign",
        "thirdness": "dicent",
        "relation": "index",
        "valid_combination": True,
        "coherence_score": 0.8,
    })
    assert adapt_observation(other)["sign_class"] == "sinsign-dicent-index"


@pytest.mark.parametrize(
    "authority_override",
    [
        {"semantic_truth": True},
        {"may_authorize": True},
        {"may_mutate_governing_state": True},
        {"kind": "canonical"},
    ],
)
def test_a_frame_claiming_authority_is_refused(authority_override) -> None:
    with pytest.raises(SemionAuthorityError):
        adapt_observation(_frame(authority=authority_override))


def test_a_forbidden_kind_is_refused_by_name() -> None:
    with pytest.raises(SemionAuthorityError):
        adapt_observation(VALID_FRAME, kind="CANONICAL_STATE")


def test_an_invalid_sign_class_is_recorded_rather_than_smoothed_over() -> None:
    """A failed classification is a result. It is carried forward AS a failure, never as a confidence."""
    evidence = adapt_observation(
        _frame(sign_class_valid=False, sign_class_errors=["thirdness: not in rheme|dicent|argument"])
    )
    assert evidence["sign_class_valid"] is False
    assert evidence["sign_class_errors"] == ["thirdness: not in rheme|dicent|argument"]
    assert evidence["status"] == "not_computable"


def test_a_specialist_lane_violation_is_surfaced() -> None:
    evidence = adapt_observation(_frame(failure="SPECIALIST_LANE_VIOLATION"))
    assert evidence["failure"] == "SPECIALIST_LANE_VIOLATION"
    assert evidence["status"] == "not_computable"


def test_assert_not_authoritative_accepts_advisory_and_rejects_the_rest() -> None:
    assert_not_authoritative(adapt_observation(VALID_FRAME))
    with pytest.raises(SemionAuthorityError):
        assert_not_authoritative({"semantic_truth": True})


def test_promotion_to_canonical_state_always_raises() -> None:
    """The boundary the manifest praises in the hyperlex instrument, mirrored exactly: there is no path
    from this adapter to canonical state, and a test holds that rather than a comment."""
    with pytest.raises(SemionAuthorityError):
        promote_to_canonical_state(adapt_observation(VALID_FRAME))


def test_a_valid_frame_maps_to_a_sign_relation_envelope() -> None:
    envelope = to_evidence_envelope(
        adapt_observation(VALID_FRAME), request_id="req-1", claim="what kind of sign is this?"
    )
    assert isinstance(envelope, EvidenceEnvelope)
    assert envelope.evidence_type == EvidenceType.SIGN_RELATION
    assert envelope.engine == "semion"
    assert envelope.candidate_outputs, "a valid frame must yield a candidate"
    assert envelope.provenance["lane"] == "shadow"
    assert envelope.provenance["influence_policy"] == "NONE"
    assert envelope.provenance["valid_for_forecast"] is False


def test_the_envelopes_confidence_is_the_frames_own_coherence() -> None:
    """Measured against the frame, not chosen: coherence_score 0.95 in, 0.95 out. The stub this replaces
    returned a fixed 0.85 for every claim, which is how a rubber stamp looks like evidence."""
    envelope = to_evidence_envelope(
        adapt_observation(VALID_FRAME), request_id="req-2", claim="c"
    )
    assert envelope.confidence == pytest.approx(0.95)


def test_an_uncomputable_frame_yields_no_candidates() -> None:
    """"I could not classify this" is a legitimate result and must not be dressed as a weak one."""
    envelope = to_evidence_envelope(
        adapt_observation(_frame(sign_class_valid=False, sign_class_errors=["x"])),
        request_id="req-3",
        claim="c",
    )
    assert envelope.candidate_outputs == []
    assert envelope.confidence == 0.0
    assert envelope.provenance["status"] == "not_computable"
