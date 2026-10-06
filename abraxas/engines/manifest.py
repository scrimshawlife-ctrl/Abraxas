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

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

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


def _spec(
    name: str,
    status: str,
    evidence_type: str,
    implementation: str,
    note: str = "",
) -> EngineSpec:
    return EngineSpec(
        name=name,
        status=status,
        evidence_type=evidence_type,
        implementation=implementation,
        note=note,
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
        "RELATIONAL_REASONING",
        "abraxas.evidence.adapters.oracle:create_oracle_adapter",
        "Factory function.",
    ),
    _spec(
        "cypher",
        LIVE,
        "RELATIONAL_REASONING",
        "abraxas.evidence.adapters.cypher:create_cypher_adapter",
        "Factory function.",
    ),
    _spec(
        "hyperlex",
        PLANNED,
        "LEXICAL_SEMANTIC",
        "",
        "HyperlexProvider exists only as a test-local class in "
        "abraxas/evidence/test_hyperlex_q1.py. abraxas/evidence/hyperlex_instrument.py "
        "defines HyperlexAuthorityError but is not an EvidenceProvider. "
        "production.py already claims this engine, so it is the closest to promotion.",
    ),
    _spec(
        "semion",
        PLANNED,
        "SIGN_RELATION",
        "",
        "SemionProvider exists only as a test-local class in "
        "abraxas/evidence/test_semion_q1.py. production.py already claims it.",
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
        "Only ResonanceFrame and DriftResonanceCoupling exist; neither is an engine.",
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
