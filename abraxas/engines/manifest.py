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

from abraxas.engines.settlement import SETTLED, Settlement

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
        "engine_name, so there is no module-level AthanorAdapter attribute. "
        "Technical settlement claimed, and its cited set is the THINNEST of the five -- stated rather than "
        "implied. There is no athanor-specific spec, fixture or receipt in this tree (its work lives in its "
        "own repository), so what holds this claim up is the parametrised conformance guard in "
        "tests/test_engine_manifest_agreement.py together with the survey's measured criteria: determinism, "
        "replay, provenance and canonical artifacts all present. A claim citing less than it appears to would "
        "be worse than no claim. Empirical and economic remain unsettled.",
        settlements=Settlement(
            technical=SETTLED,
            technical_evidence=(
                "abraxas/evidence/provider.py",
                "tests/test_engine_manifest_agreement.py",
            ),
        ),
    ),
    _spec(
        "noesis",
        LIVE,
        "LATENT_STRUCTURAL",
        "abraxas.evidence.verifiers.latent:NoesisEvidenceProvider",
        "Class. Did not subclass EvidenceProvider until the agreement guard "
        "caught it; the interface is now declared explicitly. Technical settlement claimed on the fullest "
        "evidence set of the five: the provider, its own specification, its deterministic fixtures, its "
        "qualification receipt and its Q1 suite are all in-tree and cited. Empirical and economic remain "
        "unsettled.",
        settlements=Settlement(
            technical=SETTLED,
            technical_evidence=(
                "abraxas/evidence/verifiers/latent.py",
                "abraxas/evidence/noesis_latent_v1.spec.md",
                "abraxas/evidence/test_noesis_q1.py",
                "abraxas/evidence/noesis_q1_receipt.json",
            ),
        ),
    ),
    _spec(
        "trutina",
        LIVE,
        "CALIBRATION",
        "abraxas.evidence.providers.trutina:TrutinaEvidenceProvider",
        "Technical settlement claimed. Cited set: the provider, its calibration specification, its Q1 suite "
        "and its qualification receipt. Note what is NOT claimed -- a calibration engine invites an "
        "empirical-settlement reading, but `technical` says only that it reliably meets its specification; "
        "whether its calibration is BETTER than an alternative is the empirical question, and it stays "
        "unsettled until it is measured against one.",
        settlements=Settlement(
            technical=SETTLED,
            technical_evidence=(
                "abraxas/evidence/providers/trutina.py",
                "abraxas/evidence/trutina_calibration_v1.spec.md",
                "abraxas/evidence/test_trutina_q1.py",
                "abraxas/evidence/trutina_q1_receipt.json",
            ),
        ),
    ),
    _spec(
        "oracle",
        LIVE,
        "NARRATIVE_SYNTHESIS",
        "abraxas.evidence.adapters.oracle:create_oracle_adapter",
        "Factory function. Declared RELATIONAL_REASONING until the evidence-type guard caught it -- "
        "which is the EvidenceEnvelope dataclass DEFAULT, so the field had never been filled in. "
        "Holds the FIRST technical settlement claimed in this manifest. scripts/survey_engine_settlements.py "
        "measures entry_point, conformance, collected tests, determinism, replay, provenance and canonical "
        "artifacts all PRESENT for this engine, and the claim cites its evidence; the survey exits non-zero "
        "if it ever stops being able to corroborate what is declared here. Empirical and economic remain "
        "UNSETTLED on purpose: an engine that reliably meets its specification is not thereby shown to beat "
        "a baseline, nor to produce consequences anyone adopts, and those are different claims.",
        settlements=Settlement(
            technical=SETTLED,
            technical_evidence=(
                "abraxas/evidence/adapters/oracle.py",
                "abraxas/contracts/oracle_signal_item_v2.py",
                ".abraxas/subsystems/oracle_signal_layer_v2.yaml",
                "tests/test_engine_manifest_agreement.py",
            ),
        ),
    ),
    _spec(
        "cypher",
        LIVE,
        "PERSISTENT_MEMORY",
        "abraxas.evidence.adapters.cypher:create_cypher_adapter",
        "Factory function. Declared RELATIONAL_REASONING until the evidence-type guard caught it, "
        "same dataclass-default defect as oracle. Technical settlement claimed on the narrowest set of the "
        "five -- the adapter and its behavioural suite -- and it is worth saying why that is enough here and "
        "would not be elsewhere: Cypher's surface is small and its contract is its behaviour, so there is no "
        "spec or fixture in this tree for it to be measured against. The engine's own repository holds its "
        "specification. Empirical and economic remain unsettled.",
        settlements=Settlement(
            technical=SETTLED,
            technical_evidence=(
                "abraxas/evidence/adapters/cypher.py",
                "tests/test_cypher_enhanced.py",
            ),
        ),
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
        "Still PLANNED, and now deliberately rather than pending a build-or-drop choice. The previous note "
        "read 'Zero files in the repo. Either build it or drop it from the architecture -- a name with no "
        "implementation is worse than an absent one.' Its premise no longer holds: the engine's own "
        "repository now carries a spec whose every component row reads 'Exists: no', and a provider whose "
        "produce_evidence() and get_model_identity() RAISE -- so the hazard that note described, an "
        "unimplemented name mistaken for a real one at arbitration, is closed by construction. Meanwhile "
        "the name still does work here: tests/test_engine_lifecycle_registration.py uses it as the clearest "
        "case of a registered-but-never-available engine, and dropping it would remove that case. Two "
        "measurements settle the other direction: EvidenceType.MULTIMODAL_INTEGRATION has no consumer "
        "anywhere in this tree, and building it would mean four modality encoders plus a fusion policy -- "
        "the component carrying the confidence-laundering risk -- with no demand to validate against. "
        "Build on a real multimodal consumer, not on a placeholder's existence."
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
