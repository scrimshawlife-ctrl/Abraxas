"""Canonical engine manifest — the single source of truth for engine topology.

Why this exists
---------------
The engine list was written out in three places that disagreed:

* ``abraxas/yggdrasil/coordinator.py`` listed 10 engines + ``yggdrasil`` + ``mock``
* ``abraxas/governance/production.py`` registered 5 (all mock providers)
* reality: only athanor, noesis, trutina, oracle and cypher have real
  ``EvidenceProvider`` implementations

Yggdrasil and the production registry both read this module, so the lists cannot
silently diverge again. ``tests/test_engine_manifest_agreement.py`` asserts that.

Status values
-------------
``live``    A real ``EvidenceProvider`` implementation exists.
``planned`` Named in the architecture; no implementation yet. Kept visible on
            purpose — a plan is allowed to be aspirational, a registry is not.

A ``planned`` engine must never be presented as available. See
``docs/ENGINE_TOPOLOGY.md`` for the audit that produced these labels.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from abraxas.engines.settlement import Settlement

LIVE = "live"
PLANNED = "planned"


@dataclass(frozen=True)
class EngineSpec:
    """One engine's canonical description."""

    name: str
    status: str
    evidence_type: str
    implementation: str
    note: str = ""
    settlements: Settlement = field(default_factory=Settlement)


def _spec(
    name: str,
    status: str,
    evidence_type: str,
    implementation: str,
    note: str = "",
    settlements: Settlement | None = None,
) -> EngineSpec:
    return EngineSpec(
        name=name,
        status=status,
        evidence_type=evidence_type,
        implementation=implementation,
        note=note,
        settlements=settlements or Settlement(),
    )


ENGINES: Tuple[EngineSpec, ...] = (
    _spec(
        "athanor",
        LIVE,
        "RELATIONAL_REASONING",
        "abraxas.evidence.provider:create_athanor_adapter",
        "Factory function. AthanorAdapter is built inside it and closes over "
        "engine_name, so there is no module-level AthanorAdapter attribute.",
    ),
    _spec(
        "noesis",
        LIVE,
        "LATENT_STRUCTURAL",
        "abraxas.evidence.verifiers.latent:NoesisEvidenceProvider",
        "Class. Did not subclass EvidenceProvider until the agreement guard "
        "caught it; the interface is now declared explicitly.",
    ),
    _spec(
        "trutina",
        LIVE,
        "CALIBRATION",
        "abraxas.evidence.providers.trutina:TrutinaEvidenceProvider",
    ),
    _spec(
        "oracle",
        LIVE,
        "NARRATIVE_SYNTHESIS",
        "abraxas.evidence.adapters.oracle:create_oracle_adapter",
        "Factory function. Declared RELATIONAL_REASONING until the evidence-type guard caught it -- "
        "which is the EvidenceEnvelope dataclass DEFAULT, so the field had never been filled in.",
    ),
    _spec(
        "cypher",
        LIVE,
        "PERSISTENT_MEMORY",
        "abraxas.evidence.adapters.cypher:create_cypher_adapter",
        "Factory function. Declared RELATIONAL_REASONING until the evidence-type guard caught it, "
        "same dataclass-default defect as oracle.",
    ),
    _spec(
        "hyperlex",
        PLANNED,
        "LEXICAL_SEMANTIC",
        "",
        "HyperlexProvider exists only as a class INSIDE a test "
        "(abraxas/evidence/test_hyperlex_q1.py, in the arbitration integration test). "
        "abraxas/evidence/hyperlex_instrument.py is an instrument, not a provider: its "
        "promote_to_canonical_state() ALWAYS raises HyperlexAuthorityError ('cannot "
        "become CANONICAL_STATE'), and TestHYPERLEX_Q1_PromotionBlocked asserts that "
        "block. So this is a deliberate SHADOW surface, NOT a promotion candidate -- "
        "making it live means changing its authority boundary first, not writing a "
        "provider. production.py claiming it is a separate defect."
    ),
    _spec(
        "semion",
        PLANNED,
        "SIGN_RELATION",
        "",
        "Instrument only, and deliberately not a provider. abraxas/evidence/semion_instrument.py "
        "now exists: it CONSUMES a semion.sign.v1 frame and maps it to the canonical "
        "EvidenceEnvelope (to_evidence_envelope), refusing semantic_truth / may_authorize / "
        "may_mutate_governing_state frames and raising on promotion -- the same boundary "
        "hyperlex_instrument holds, mirrored deliberately. It does NOT classify: Semion's own docs "
        "declare the direction ('Semion does not import Abraxas. Abraxas may consume this dict at "
        "RUNE.SEMIOSIS.CHAIN'), so the classifier stays in the Semion repository and a second one "
        "here would invert that dependency. It stays PLANNED, not live, for the same reason as "
        "hyperlex: an instrument is not a registered provider, and promotion is an authority "
        "decision, not a missing-code problem. This note previously said nothing here could emit "
        "an EvidenceEnvelope and that no instrument module existed; both were true when written "
        "and are now recorded as fixed rather than quietly deleted."
    ),
    _spec(
        "chronos",
        PLANNED,
        "",
        "",
        "No implementation found anywhere in the repo.",
    ),
    _spec(
        "resonance",
        PLANNED,
        "",
        "",
        "The phase layer exists -- abraxas/phase/detector.py (PhaseAlignmentDetector, "
        "SynchronicityMap), coupling.py (CouplingDetector) and early_warning.py "
        "(EarlyWarningSystem) -- along with ResonanceFrame and DriftResonanceCoupling. Those are "
        "detectors and data structures, not a provider: abraxas.evidence.adapters.resonance does "
        "not exist, so nothing here can emit an EvidenceEnvelope. The sibling Resonance repo now "
        "composes them into a provider, but it is not an installed dependency, so no entry point "
        "resolves from this tree and the engine stays planned. This note previously claimed that "
        "only ResonanceFrame and DriftResonanceCoupling existed, which understated the phase layer.",
    ),
    _spec(
        "aether",
        PLANNED,
        "",
        "",
        "Zero files in the repo. Either build it or drop it from the architecture — "
        "a name with no implementation is worse than an absent one.",
    ),
)

#: Test doubles. Registered so the rune registry accepts them, never a real engine.
TEST_DOUBLES: Tuple[str, ...] = ("mock",)

#: Yggdrasil itself is the coordinator, not one of the engines it routes to.
COORDINATOR = "yggdrasil"


def all_engine_names() -> Tuple[str, ...]:
    """Every declared engine name, in manifest order."""
    return tuple(spec.name for spec in ENGINES)


def live_engines() -> Tuple[str, ...]:
    """Engines with a real implementation."""
    return tuple(spec.name for spec in ENGINES if spec.status == LIVE)


def planned_engines() -> Tuple[str, ...]:
    """Engines declared but not yet implemented."""
    return tuple(spec.name for spec in ENGINES if spec.status == PLANNED)


def registrable_names() -> Tuple[str, ...]:
    """Names Yggdrasil's rune registry should accept.

    Every declared engine plus the coordinator and the test double. Includes
    ``planned`` engines deliberately: registering the *name* keeps future engines
    addressable without implying an implementation exists.
    """
    return all_engine_names() + (COORDINATOR,) + TEST_DOUBLES


def get(name: str) -> Optional[EngineSpec]:
    """Look up an engine by name, or ``None``."""
    for spec in ENGINES:
        if spec.name == name:
            return spec
    return None


def by_status() -> Dict[str, Tuple[str, ...]]:
    """Engine names grouped by status."""
    grouped: Dict[str, list] = {}
    for spec in ENGINES:
        grouped.setdefault(spec.status, []).append(spec.name)
    return {status: tuple(names) for status, names in grouped.items()}


__all__ = [
    "LIVE",
    "PLANNED",
    "COORDINATOR",
    "TEST_DOUBLES",
    "ENGINES",
    "EngineSpec",
    "all_engine_names",
    "live_engines",
    "planned_engines",
    "registrable_names",
    "get",
    "by_status",
]
