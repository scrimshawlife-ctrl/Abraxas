"""Semion Instrument V1 → Abraxas shadow evidence adapter.

Feature-gated SHADOW lane. Semion is an observation / evidence source only.

```text
SEMION_OUTPUT != SEMANTIC_TRUTH
influence_policy = NONE
valid_for_forecast = false
lane = shadow
```

Mirrors the contract of ``abraxas/evidence/hyperlex_instrument.py`` — the comparison point the engine
manifest itself names — because both engines are deliberate SHADOW surfaces whose output must never acquire
authority.

WHY THIS MODULE EXISTS AT ALL

The engine manifest recorded that Semion's provider *"exists only as a class INSIDE a test"* and that
*"there is no instrument module at all"*. That test-only provider **ignored its claim** and returned a
hardcoded ``answer="qualisign-rheme-icon"`` at a fixed ``confidence=0.85``: a rubber stamp with a confidence
value attached. Extracting it into a real module would have shipped exactly that.

So this instrument **CONSUMES a classification; it does not produce one.** Semion's own docs declare the
direction — *"Semion does not import Abraxas. Abraxas may consume this dict at RUNE.SEMIOSIS.CHAIN."* The
classifier lives in the Semion repository (``src/semion/classify.py``); a second classifier here would be a
second source of truth **and** would invert the declared dependency.

Wire shape: ``semion.sign.v1`` / ``SEMION_SIGN_RELATION_V1``, from
``abraxas/evidence/semion_sign_relation_v1.spec.md`` § 3.1 and ``semion_q1_fixtures.yaml``.
"""

from __future__ import annotations

import os
from typing import Any, Mapping, NoReturn, Optional

SCHEMA = "abraxas.evidence.semion_instrument.v1"
ALLOWED_KINDS = ("OBSERVATION", "EVIDENCE", "SHADOW_SIGNAL")
FORBIDDEN_KINDS = ("CANONICAL_STATE", "GOLD", "FINAL_INTERPRETATION", "AUTHORIZATION")

CONTRACT_VERSION = "semion.sign.v1"
INSTRUMENT_VERSION = "SEMION_SIGN_RELATION_V1"
ENGINE_NAME = "semion"
ENGINE_VERSION = "semion.sign.v1"
MODEL_IDENTITY = "semion-sign-v1"

#: Named by the SEMION-Q1 spec itself: "Feature flag: ABX_SEMION_INSTRUMENT (defaults off)".
FEATURE_ENV = "ABX_SEMION_INSTRUMENT"

_DEFAULT_KIND = "SHADOW_SIGNAL"
_FAILURE_STATES = frozenset({"NOT_COMPUTABLE", "SPECIALIST_LANE_VIOLATION"})


class SemionAuthorityError(ValueError):
    """Semion evidence claimed authority it cannot hold, or attempted an authoritative promotion."""


def instrument_enabled() -> bool:
    """Shadow integration disabled by default — the spec says the flag defaults off."""
    return os.environ.get(FEATURE_ENV, "0").strip() in {"1", "true", "TRUE", "yes", "YES"}


def _require_advisory_authority(observation: Mapping[str, Any]) -> None:
    """Every authority claim in the frame is true-or-refuse.

    The test-only provider this replaces carried these fields as decoration. Here they are load-bearing:
    a frame asserting any of them raises instead of being adapted.
    """
    authority = observation.get("authority") or {}
    if authority.get("semantic_truth") is True:
        raise SemionAuthorityError(
            "refusing semantic_truth=true observation — SEMION_OUTPUT != SEMANTIC_TRUTH"
        )
    if authority.get("may_authorize") is True:
        raise SemionAuthorityError("refusing may_authorize=true observation")
    if authority.get("may_mutate_governing_state") is True:
        raise SemionAuthorityError("refusing may_mutate_governing_state=true observation")
    if authority.get("kind") not in (None, "advisory"):
        raise SemionAuthorityError(
            f"observation authority must be advisory; got {authority.get('kind')!r}"
        )


def adapt_observation(
    observation: Mapping[str, Any],
    *,
    kind: str = _DEFAULT_KIND,
) -> dict[str, Any]:
    """Translate a ``semion.sign.v1`` observation → Abraxas advisory evidence.

    Consumes a classification; does not perform one. The ``sign_class`` and ``peircean_analysis`` returned
    are the frame's own — this function has no classifier to fall back on, by design.
    """
    if kind not in ALLOWED_KINDS:
        raise SemionAuthorityError(f"kind must be one of {ALLOWED_KINDS}; got {kind!r}")
    if kind in FORBIDDEN_KINDS:
        raise SemionAuthorityError(f"forbidden authoritative kind: {kind!r}")

    _require_advisory_authority(observation)

    failure = observation.get("failure")
    sign_class_valid = bool(observation.get("sign_class_valid"))
    computable = sign_class_valid and failure not in _FAILURE_STATES

    relation_steps: list[dict[str, Any]] = []
    for step in observation.get("relation_steps") or []:
        if not isinstance(step, Mapping):
            continue
        relation_steps.append(
            {
                "relation": step.get("relation"),
                "subject": step.get("subject"),
                "object": step.get("object"),
                "result": step.get("result"),
                "confidence": float(step.get("confidence") or 0.0),
                "metadata": dict(step.get("metadata") or {}),
            }
        )

    provenance = dict(observation.get("provenance") or {})

    return {
        "schema": SCHEMA,
        "kind": kind,
        "observation_id": observation.get("observation_id"),
        "sign_class": observation.get("sign_class"),
        "sign_class_valid": sign_class_valid,
        "sign_class_errors": list(observation.get("sign_class_errors") or []),
        "interpretant_coherence": observation.get("interpretant_coherence"),
        "representamen_object_alignment": observation.get("representamen_object_alignment"),
        "peircean_analysis": observation.get("peircean_analysis"),
        "relation_steps": relation_steps,
        "failure": failure,
        "status": "computable" if computable else "not_computable",
        # The boundary, carried on the artifact rather than asserted in prose.
        "lane": "shadow",
        "influence_policy": "NONE",
        "valid_for_forecast": False,
        "semantic_truth": False,
        "authority": "advisory",
        "source": provenance.get("instrument_version") or INSTRUMENT_VERSION,
        "contract_version": provenance.get("contract_version") or CONTRACT_VERSION,
        "ontology_version": provenance.get("ontology_version"),
        "provenance": provenance,
    }


def assert_not_authoritative(evidence: Mapping[str, Any]) -> None:
    """Re-assert the boundary on an adapted payload, for callers that receive one from elsewhere.

    Checks the artifact rather than the input: an evidence dict assembled by other code still has to carry
    the shadow lane, no influence, and no forecast eligibility to pass here.
    """
    if evidence.get("semantic_truth") is True:
        raise SemionAuthorityError("evidence claims semantic truth")
    if evidence.get("lane") != "shadow":
        raise SemionAuthorityError(f"evidence lane must be shadow; got {evidence.get('lane')!r}")
    if evidence.get("influence_policy") != "NONE":
        raise SemionAuthorityError(
            f"evidence influence_policy must be NONE; got {evidence.get('influence_policy')!r}"
        )
    if evidence.get("valid_for_forecast") is not False:
        raise SemionAuthorityError(
            f"evidence valid_for_forecast must be False; got {evidence.get('valid_for_forecast')!r}"
        )


def promote_to_canonical_state(evidence: Mapping[str, Any]) -> NoReturn:
    """There is no path from Semion evidence to canonical state through this adapter.

    Mirrors ``hyperlex_instrument.promote_to_canonical_state`` exactly, including raising rather than
    returning a refusal object: a caller that ignores a return value would otherwise proceed as though the
    promotion had happened. A test holds this rather than a comment.
    """
    raise SemionAuthorityError(
        "Semion evidence cannot become CANONICAL_STATE through this adapter"
    )


def to_evidence_envelope(
    evidence: Mapping[str, Any],
    *,
    request_id: str,
    claim: str,
) -> "EvidenceEnvelope":
    """Map validated advisory evidence → the canonical ``EvidenceEnvelope``.

    The confidence is the frame's **own** ``coherence_score``. Nothing here chooses a number: an
    uncomputable frame yields **no candidates** at ``confidence=0.0``, because *"I could not classify this"*
    is a result and must not be dressed as a weak one.
    """
    from abraxas.evidence.contract import (
        CandidateOutput,
        EvidenceEnvelope,
        EvidenceType,
        RelationStep,
    )

    assert_not_authoritative(evidence)

    peircean = evidence.get("peircean_analysis") or {}
    candidates: list[CandidateOutput] = []
    confidence = 0.0

    if evidence.get("status") == "computable":
        confidence = float(peircean.get("coherence_score") or 0.0)
        steps = [
            RelationStep(
                relation=str(step.get("relation")),
                subject=str(step.get("subject")),
                object=str(step.get("object")),
                result=str(step.get("result")),
                confidence=float(step.get("confidence") or 0.0),
                metadata=dict(step.get("metadata") or {}),
            )
            for step in evidence.get("relation_steps") or []
        ]
        trace = "Peircean: {existence}-{thirdness}-{relation}".format(
            existence=peircean.get("existence"),
            thirdness=peircean.get("thirdness"),
            relation=peircean.get("relation"),
        )
        candidates.append(
            CandidateOutput(
                answer=str(evidence.get("sign_class")),
                confidence=confidence,
                reasoning_trace=trace,
                relation_steps=steps,
            )
        )

    return EvidenceEnvelope(
        engine=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        model_identity=MODEL_IDENTITY,
        request_id=request_id,
        claim=claim,
        candidate_outputs=candidates,
        evidence_type=EvidenceType.SIGN_RELATION,
        reasoning_steps=[],
        relations=[str(step.get("relation")) for step in evidence.get("relation_steps") or []],
        confidence=confidence,
        uncertainty=1.0 - confidence,
        decision_margin=0.0,
        entropy=0.0,
        provenance={
            "source": MODEL_IDENTITY,
            "method": "semion_sign_relation_adapter",
            "status": evidence.get("status"),
            "lane": evidence.get("lane"),
            "influence_policy": evidence.get("influence_policy"),
            "valid_for_forecast": evidence.get("valid_for_forecast"),
            "semantic_truth": evidence.get("semantic_truth"),
            "sign_class": evidence.get("sign_class"),
            "sign_class_valid": evidence.get("sign_class_valid"),
            "sign_class_errors": evidence.get("sign_class_errors"),
            "failure": evidence.get("failure"),
            "contract_version": evidence.get("contract_version"),
            "ontology_version": evidence.get("ontology_version"),
            "frame_provenance": evidence.get("provenance"),
        },
    )


def classify_via_semion(atom: Mapping[str, Any]) -> dict[str, Any]:
    """Optional live call into the Semion repository's own classifier, when enabled and installed.

    Requires the ``semion`` package (the Semion repository) on ``PYTHONPATH``. Disabled by default, and
    never used by the adapter path: the wire-shape adaptation works on observation dicts alone, so Abraxas
    needs no dependency on the engine repository to consume its output.
    """
    if not instrument_enabled():
        raise SemionAuthorityError(
            f"Semion classification is disabled; set {FEATURE_ENV}=1 and install the semion package"
        )
    try:
        from semion import classify  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - exercised only when enabled and uninstalled
        raise SemionAuthorityError(
            "the semion package is not installed; install the Semion repository to classify atoms"
        ) from exc
    result: Optional[dict[str, Any]] = dict(classify(atom))
    if result is None:  # pragma: no cover - defensive
        raise SemionAuthorityError("semion.classify returned no frame")
    return result
