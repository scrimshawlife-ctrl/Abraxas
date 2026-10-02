"""Hyperlex Instrument V1 → Abraxas shadow evidence adapter.

Feature-gated SHADOW lane. Hyperlex is an observation / evidence source only.

```text
HYPERLEX_OUTPUT != SEMANTIC_TRUTH
influence_policy = NONE
valid_for_forecast = false
```

Does not import Hyperlex unless ABX_HYPERLEX_INSTRUMENT is enabled and the
package is installed. Wire-shape adaptation works on observation dicts alone.
"""

from __future__ import annotations

import os
from typing import Any, Mapping, Optional

SCHEMA = "abraxas.evidence.hyperlex_instrument.v1"
ALLOWED_KINDS = ("OBSERVATION", "EVIDENCE", "SHADOW_SIGNAL")
FORBIDDEN_KINDS = ("CANONICAL_STATE", "GOLD", "FINAL_INTERPRETATION", "AUTHORIZATION")

FEATURE_ENV = "ABX_HYPERLEX_INSTRUMENT"


class HyperlexAuthorityError(ValueError):
    """Hyperlex evidence attempted an authoritative promotion."""


def instrument_enabled() -> bool:
    """Shadow integration disabled by default."""
    return os.environ.get(FEATURE_ENV, "0").strip() in {"1", "true", "TRUE", "yes", "YES"}


def adapt_observation(
    observation: Mapping[str, Any],
    *,
    kind: str = "SHADOW_SIGNAL",
) -> dict[str, Any]:
    """Translate HyperlexObservation wire shape → Abraxas advisory evidence."""
    if kind not in ALLOWED_KINDS:
        raise HyperlexAuthorityError(
            f"kind must be one of {ALLOWED_KINDS}; got {kind!r}"
        )
    if kind in FORBIDDEN_KINDS:
        raise HyperlexAuthorityError("forbidden authoritative kind")

    auth = observation.get("authority") or {}
    if auth.get("semantic_truth") is True:
        raise HyperlexAuthorityError("refusing semantic_truth=true observation")
    if auth.get("kind") not in (None, "advisory"):
        raise HyperlexAuthorityError("observation authority must be advisory")

    candidates_out = []
    for c in observation.get("candidates") or []:
        if not isinstance(c, dict):
            continue
        if c.get("advisory") is not True:
            raise HyperlexAuthorityError("non-advisory candidate blocked at boundary")
        candidates_out.append(
            {
                "concept_id": c.get("concept_id"),
                "score": c.get("score"),
                "axis": c.get("axis"),
                "advisory": True,
                "status": c.get("status", "advisory"),
            }
        )

    evidence = observation.get("evidence") or {}
    diagnostics = observation.get("diagnostics") or {}
    representation = observation.get("representation") or {}
    provenance = observation.get("provenance") or {}

    return {
        "schema": SCHEMA,
        "kind": kind,
        "source": "hyperlex",
        "authority": "advisory",
        "semantic_truth": False,
        "may_authorize": False,
        "may_mutate_governing_state": False,
        "may_override_provenance": False,
        "observation_id": observation.get("observation_id"),
        "input_hash": observation.get("input_hash"),
        "evidence": {
            "present": bool(evidence.get("present")),
            "score": evidence.get("score"),
            "abstain": bool(evidence.get("abstain")),
            "reason": evidence.get("reason"),
        },
        "candidates": candidates_out,
        "neighborhood": list(observation.get("neighborhood") or []),
        "ambiguity": diagnostics.get("ambiguity"),
        "margin": diagnostics.get("margin"),
        "diagnostics": {
            "distribution_distance": diagnostics.get("distribution_distance"),
            "representation_drift": diagnostics.get("representation_drift"),
            "unavailable": list(diagnostics.get("unavailable") or []),
        },
        "representation": {
            "encoder_id": representation.get("encoder_id"),
            "encoder_hash": representation.get("encoder_hash"),
            "embed_mode": representation.get("embed_mode"),
            "embedding_ref": representation.get("embedding_ref"),
        },
        "instrument_version": provenance.get("instrument_version"),
        "ontology_version": provenance.get("ontology_version"),
        "contract_version": provenance.get("contract_version"),
        "manifest_sha256": provenance.get("manifest_sha256"),
        "schema_sha256": provenance.get("schema_sha256"),
        "settlement_ref": provenance.get("settlement_ref"),
        "settlement_receipt": provenance.get("settlement_receipt"),
        "artifact_hashes": dict(provenance.get("artifact_hashes") or {}),
        "influence_policy": "NONE",
        "valid_for_forecast": False,
        "lane": "shadow",
        "enabled": instrument_enabled(),
        "notes": [
            "HYPERLEX_OUTPUT != SEMANTIC_TRUTH",
            "Consume as OBSERVATION/EVIDENCE/SHADOW_SIGNAL only.",
            "Downstream Abraxas reasoning may verify; must not auto-promote.",
        ],
    }


def assert_not_authoritative(evidence: Mapping[str, Any]) -> None:
    if evidence.get("semantic_truth") is True:
        raise HyperlexAuthorityError("semantic_truth must be false")
    if evidence.get("authority") != "advisory":
        raise HyperlexAuthorityError("authority must be advisory")
    if evidence.get("may_authorize") is True:
        raise HyperlexAuthorityError("may_authorize must be false")
    if evidence.get("may_mutate_governing_state") is True:
        raise HyperlexAuthorityError("may_mutate_governing_state must be false")
    if evidence.get("kind") in FORBIDDEN_KINDS:
        raise HyperlexAuthorityError("kind must not be authoritative")
    if evidence.get("valid_for_forecast") is True:
        raise HyperlexAuthorityError("valid_for_forecast must be false")
    if evidence.get("influence_policy") not in (None, "NONE"):
        raise HyperlexAuthorityError("influence_policy must be NONE")


def promote_to_canonical_state(evidence: Mapping[str, Any]) -> dict[str, Any]:
    raise HyperlexAuthorityError(
        "Hyperlex evidence cannot become CANONICAL_STATE through this adapter"
    )


def observe_text(text: str, *, requested: Optional[list[str]] = None) -> dict[str, Any]:
    """Optional live call into Hyperlex Instrument when feature-enabled.

    Requires ``hyperlex`` package on PYTHONPATH. Disabled by default.
    """
    if not instrument_enabled():
        return {
            "ok": False,
            "error": "ABX_HYPERLEX_INSTRUMENT_disabled",
            "lane": "shadow",
            "enabled": False,
        }
    try:
        from hyperlex.instrument import observe as hlx_observe
    except ImportError as exc:
        return {
            "ok": False,
            "error": "hyperlex_not_installed",
            "detail": str(exc),
            "enabled": True,
        }
    obs = hlx_observe(text, requested=requested)
    evidence = adapt_observation(obs, kind="SHADOW_SIGNAL")
    assert_not_authoritative(evidence)
    return {"ok": True, "observation": obs, "evidence": evidence, "enabled": True}
