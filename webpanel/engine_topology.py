"""Render-ready engine topology, read from the live Yggdrasil registry.

Honest by construction, matching the Inference card's precedent in
templates/operator_console.html: this reads the registry at call time, so it cannot claim an
engine that was removed, and it cannot drift from the registry the way a hardcoded list would.

The registry is the single source of truth. If you find yourself typing an engine name in
this file, stop -- that is the drift this module exists to prevent.

Accessors used (verified against the live registry, not assumed):
    registry.list_engines()          -> List[str]
    registry.get_engine_rune(name)   -> EngineRune(engine_name, status, metadata, ...)
    registry.is_engine_available(n)  -> bool
    registry.get_registry_stats()    -> RegistryStats(total_engines, active_engines, ...)

EngineRune.metadata carries the manifest's own fields:
    {'evidence_type': 'RELATIONAL_REASONING', 'implementation': '...', 'manifest_status': 'live'}
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Names that live in the registry but are NOT engines to be started. Classified, not
# dropped -- dropping them would hide that the registry contains them.
_COORDINATOR = "yggdrasil"
_TEST_DOUBLE = "mock"

# Engines KNOWN to need no model: they consume inputs supplied to them (latent captures,
# forecasts, memory, rune/phase logic, sign frames) and have no inference step to serve.
#
# This is a DECLARED fact, not a measured one. The registry does not carry it, so where an
# engine is not listed here AND is not implemented, the card must say "unknown" rather than
# "needs a model" -- see _model_requirement. Claiming a model requirement for an engine with
# no implementation is the same defect class as presenting a planned engine as available.
_DECLARED_NO_MODEL = frozenset(
    {"noesis", "trutina", "cypher", "chronos", "resonance", "semion"}
)

# "yes" / "no" / "unknown" -- deliberately three-valued. A boolean forced a confident answer
# where the repo has no evidence.
MODEL_YES = "yes"
MODEL_NO = "no"
MODEL_UNKNOWN = "unknown"


def _model_requirement(engine_name: str, state: str, has_implementation: bool) -> str:
    """Does this engine need a model? Answer only from what the repo actually knows.

    An engine that is not implemented cannot have a model requirement -- there is no
    inference step to serve. Saying "yes" there would be an assertion about code that does
    not exist, so it returns MODEL_UNKNOWN, and the template renders that honestly.
    """
    if engine_name in _DECLARED_NO_MODEL:
        return MODEL_NO
    if state == "planned" or not has_implementation:
        return MODEL_UNKNOWN
    return MODEL_YES


def _state_for(status: Any) -> str:
    """Map an EngineStatus to the card's three visual states.

    Returns one of: "active" | "planned" | "unavailable".

    "planned" MUST stay distinct from "active". The registry's EngineStatus docstring
    records that collapsing these made `aether` (deliberately planned, zero files)
    identical to `athanor` (a working provider), which the manifest forbids:
    "A planned engine must never be presented as available."
    """
    name = getattr(status, "name", str(status)).upper()
    if name == "ACTIVE":
        return "active"
    if name == "PLANNED":
        return "planned"
    return "unavailable"


def _classify(engine_name: str) -> str:
    """Is this row an engine, the coordinator, or a test double?"""
    if engine_name == _COORDINATOR:
        return "coordinator"
    if engine_name == _TEST_DOUBLE:
        return "test_double"
    return "engine"


def _metadata_for(registry: Any, engine_name: str) -> Dict[str, Any]:
    """The engine's own manifest metadata, or an empty dict.

    Read from the registry -- never inferred from the name.
    """
    try:
        rune = registry.get_engine_rune(engine_name)
        meta = getattr(rune, "metadata", None)
        return meta if isinstance(meta, dict) else {}
    except Exception:
        return {}


def build_engine_topology() -> Dict[str, Any]:
    """Read the live registry and shape it for the template.

    Never raises: a broken registry must degrade to an empty card with a visible reason,
    not a 500 on the operator console. The console is the surface an operator uses to find
    out that something is broken, so it must not be the thing that breaks.
    """
    rows: List[Dict[str, Any]] = []
    error: str | None = None

    try:
        from abraxas.yggdrasil.coordinator import YggdrasilCoordinator

        coord = YggdrasilCoordinator()
        try:
            coord.initialize()
        except Exception as exc:  # registry may already be initialised
            logger.debug("coordinator.initialize(): %s", exc)

        registry = coord.rune_registry

        for name in sorted(registry.list_engines()):
            rune = registry.get_engine_rune(name)
            state = _state_for(getattr(rune, "status", None))
            kind = _classify(name)
            meta = _metadata_for(registry, name)
            rows.append(
                {
                    "name": name,
                    "state": state,
                    "kind": kind,
                    "available": bool(registry.is_engine_available(name)),
                    "evidence_type": str(meta.get("evidence_type") or ""),
                    "manifest_status": str(meta.get("manifest_status") or ""),
                    "implementation": str(meta.get("implementation") or ""),
                    "model_requirement": (
                        _model_requirement(name, state, bool(meta.get("implementation")))
                        if kind == "engine"
                        else MODEL_NO
                    ),
                    # the grouping used by the template: only a declared "yes" or "no" is a
                    # claim; "unknown" is listed separately rather than folded into either
                    "needs_model": (
                        kind == "engine"
                        and _model_requirement(name, state, bool(meta.get("implementation")))
                        == MODEL_YES
                    ),
                }
            )
    except Exception as exc:
        logger.warning("could not read the engine registry: %s", exc)
        error = f"{type(exc).__name__}: {exc}"

    # ALL engine-kind rows, regardless of model requirement. Counting only the ones with a
    # declared requirement silently dropped the unknown ones: counts said 8 engines and 3
    # planned when there are 10 and 5. The card must not lose rows because a fact is
    # undeclared -- an unknown is still an engine.
    engines = [r for r in rows if r["kind"] == "engine"]
    undeclared = [r for r in engines if r["model_requirement"] == MODEL_UNKNOWN]
    counts = {
        "total": len(rows),
        "engines": len(engines),
        "active": sum(1 for r in engines if r["state"] == "active"),
        "planned": sum(1 for r in engines if r["state"] == "planned"),
        "other": sum(1 for r in engines if r["state"] == "unavailable"),
        "coordinator": sum(1 for r in rows if r["kind"] == "coordinator"),
        "test_double": sum(1 for r in rows if r["kind"] == "test_double"),
    }

    return {
        "engines": rows,
        "counts": counts,
        "error": error,
        # grouped views, so the template does not have to sort or filter
        "needs_model": [r for r in engines if r["model_requirement"] == MODEL_YES],
        "no_model": [r for r in engines if r["model_requirement"] == MODEL_NO],
        "model_unknown": undeclared,
        "non_engines": [r for r in rows if r["kind"] != "engine"],
    }
