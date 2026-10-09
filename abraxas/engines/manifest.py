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
        LIVE,
        "LEXICAL_SEMANTIC",
        "abraxas.evidence.providers.hyperlex:create_hyperlex_adapter",
        "Real factory consuming hyperlex_instrument (shadow boundary, feature-gated). Authority: advisory, influence_policy=NONE, no semantic_truth. Per sibling /Users/appliedalchemylabs/Hyperlex/DESIGN.md, /Users/appliedalchemylabs/Hyperlex/SPEC.md and docs/SIBLING_REPOS.md. Technical settlement cited on the provider, its instrument, the integration doc, and the sibling contract. Empirical and economic remain unsettled.",
        settlements=Settlement(
            technical=SETTLED,
            technical_evidence=(
                "abraxas/evidence/providers/hyperlex.py",
                "abraxas/evidence/hyperlex_instrument.py",
                "docs/integration/hyperlex_instrument_v1.md",
                "docs/SIBLING_REPOS.md",
                "tests/test_hyperlex_provider_real.py",
            ),
        ),
    ),
    _spec(
        "semion",
        LIVE,
        "SIGN_RELATION",
        "abraxas.evidence.providers.semion:create_semion_adapter",
        "Real factory consuming semion_instrument (shadow boundary, feature-gated). Authority: advisory, influence_policy=NONE. Per sibling /Users/appliedalchemylabs/Semion/ARCHITECTURE.md and docs/SIBLING_REPOS.md. Semion states its own direction: 'Semion does not import Abraxas. Abraxas may consume this dict.' Technical settlement cited on the provider and its instrument. Empirical and economic remain unsettled.",
        settlements=Settlement(
            technical=SETTLED,
            technical_evidence=(
                "abraxas/evidence/providers/semion.py",
                "abraxas/evidence/semion_instrument.py",
                "docs/SIBLING_REPOS.md",
                "tests/test_semion_provider_real.py",
            ),
        ),
    ),
    _spec(
        "chronos",
        LIVE,
        "TEMPORAL_REASONING",
        "abraxas.evidence.providers.chronos:create_chronos_adapter",
        "Real factory composing in-tree runes (SCAN → ALIGN → OVERLAY → PACKET). Lane: SHADOW, authority: advisory, no forecast influence. Per sibling /Users/appliedalchemylabs/Chronos/SPEC.md and docs/SIBLING_REPOS.md. Chronos owns no temporal logic of its own — the four ABX-Runes are the implementation. Technical settlement cited on the provider, rune operators, governance records, and sibling SPEC. Empirical and economic remain unsettled.",
        settlements=Settlement(
            technical=SETTLED,
            technical_evidence=(
                "abraxas/evidence/providers/chronos.py",
                "abraxas/runes/operators/chrono_scan.py",
                "abraxas/runes/operators/chrono_align.py",
                "abraxas/runes/operators/chrono_overlay.py",
                "abraxas/runes/operators/chrono_packet.py",
                ".abraxas/subsystems/rune_chrono_scan_v0.yaml",
                ".abraxas/subsystems/rune_chrono_align_v0.yaml",
                ".abraxas/subsystems/rune_chrono_overlay_v0.yaml",
                ".abraxas/subsystems/rune_chrono_packet_v0.yaml",
                "docs/SIBLING_REPOS.md",
                "tests/test_chronos_provider_real.py",
            ),
        ),
    ),
    _spec(
        "resonance",
        LIVE,
        "RESONANCE_ANALYSIS",
        "abraxas.evidence.providers.resonance:create_resonance_adapter",
        "Real factory composing abraxas.phase detectors (PhaseAlignmentDetector + CouplingDetector). Detects cross-domain phase alignments and drift-resonance coupling. Compute: CPU, no model. Per sibling /Users/appliedalchemylabs/Resonance/SPEC.md and docs/SIBLING_REPOS.md. Technical settlement cited on the provider, phase layer detectors, and sibling SPEC. Empirical and economic remain unsettled.",
        settlements=Settlement(
            technical=SETTLED,
            technical_evidence=(
                "abraxas/evidence/providers/resonance.py",
                "abraxas/phase/detector.py",
                "abraxas/phase/coupling.py",
                "docs/SIBLING_REPOS.md",
                "tests/test_resonance_provider_real.py",
            ),
        ),
    ),
    _spec(
        "aether",
        PLANNED,
        "MULTIMODAL_INTEGRATION",
        "abraxas.evidence.providers.aether:create_aether_adapter",
        "Refuses via AetherNotImplemented on produce_evidence/get_model_identity. "
        "Deliberate fail-closed test case per sibling /Users/appliedalchemylabs/Aether/SPEC.md §5. "
        "Lane: SHADOW, advisory only, influence=NONE. Technical settlement on the refusing boundary "
        "and sibling spec (no real fusion/encoders exist). Empirical and economic remain unsettled.",
        settlements=Settlement(
            technical=SETTLED,
            technical_evidence=(
                "abraxas/evidence/providers/aether.py",
                "tests/test_aether_provider.py",
                "docs/SIBLING_REPOS.md",
                "/Users/appliedalchemylabs/Aether/SPEC.md",
            ),
        ),
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
