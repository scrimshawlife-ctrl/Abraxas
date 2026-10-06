"""
Yggdrasil Engine Registry — Source of Truth for Engine Registration

This module implements the rune-based engine registry that serves as the
source of truth for all registered engines in the Yggdrasil system.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    """Default clock: current UTC, ISO-8601. Injected away in tests."""
    return datetime.now(timezone.utc).isoformat()


class EngineStatus(str, Enum):
    """Registry lifecycle for a registered name.

    ``PLANNED`` exists so the canonical manifest's live/planned distinction SURVIVES
    registration. Without it every registered name was stamped ``REGISTERED``, which
    made ``aether`` (zero files anywhere in the repo) indistinguishable from
    ``athanor`` (a working provider) — the exact condition the manifest forbids:

        "A ``planned`` engine must never be presented as available."

    ``ACTIVE`` therefore means "a real EvidenceProvider exists", and it is the only
    status that counts as available.
    """

    ACTIVE = "active"          # live engine: a real EvidenceProvider implementation
    PLANNED = "planned"        # named in the architecture; no implementation yet
    REGISTERED = "registered"  # addressable, but not an engine: the coordinator, a
                               # test double, or one ABX-Rune capability
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    FAILED = "failed"


def status_for(engine_name: str) -> EngineStatus:
    """Translate the canonical manifest's status into a registry lifecycle value.

    ``abraxas.engines.manifest`` decides live vs planned; this only maps it. Names that
    are not engines at all — the coordinator, test doubles, individual rune
    capabilities such as ``ϟ₁`` or ``RUNE.FIND_SKILLS`` — are ``REGISTERED``:
    addressable, but never counted as live engines.
    """
    from abraxas.engines.manifest import COORDINATOR, LIVE, TEST_DOUBLES, get

    if engine_name in TEST_DOUBLES or engine_name == COORDINATOR:
        return EngineStatus.REGISTERED

    spec = get(engine_name)
    if spec is None:
        return EngineStatus.REGISTERED
    return EngineStatus.ACTIVE if spec.status == LIVE else EngineStatus.PLANNED


@dataclass
class EngineRune:
    """Represents an engine's rune in the registry."""
    engine_name: str
    status: EngineStatus
    registered_at: str
    last_updated: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    rune_hash: str = ""  # Cryptographic hash of engine identity


@dataclass
class RegistryStats:
    """Statistics for the rune registry."""
    total_engines: int = 0
    active_engines: int = 0
    registered_today: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class YggdrasilEngineRegistry:
    """Registry for tracking engine runes and registration status."""
    
    def __init__(self, clock: Optional[Callable[[], str]] = None):
        """``clock`` returns an ISO-8601 UTC timestamp string.

        Injectable so registration is reproducible: a test can pin it and compare two
        registries exactly, instead of racing the wall clock.
        """
        self._engines: Dict[str, EngineRune] = {}
        self._initialized = False
        self._clock = clock or _utc_now_iso
        logger.info("Yggdrasil Engine Registry initialized")
    
    def initialize(self) -> None:
        """Initialize the registry by loading the ABX-Runes capability bindings.

        This module declares itself the source of truth for engine registration, but it
        had NO wiring to the rune registry: `abraxas/runes/registry.py` holds the 117
        bindings, and nothing here imported them, while nothing there imported this.
        Loading them is what makes this registry actually authoritative rather than a
        placeholder.
        """
        if self._initialized:
            return
        self.load_rune_bindings()
        self._initialized = True
        logger.debug("Yggdrasil Engine Registry fully initialized")

    def load_rune_bindings(self, registry_path: Optional[Any] = None) -> int:
        """Register every ABX-Rune binding as an engine. Returns the number loaded.

        The direction is rune data INTO the Yggdrasil plane: ABX-Runes define WHAT may be
        done, YGGDRASIL defines HOW bounded capabilities connect.
        """
        from abraxas.runes.registry import load_registry

        loaded = 0
        for binding in load_registry(registry_path):
            self.register_engine(
                binding.rune_id,
                {
                    "capability": binding.capability,
                    "operator_path": binding.operator_path,
                    "inputs": list(binding.inputs or []),
                    "outputs": list(binding.outputs or []),
                },
            )
            loaded += 1
        logger.info(f"Loaded {loaded} ABX-Rune bindings into the Yggdrasil registry")
        return loaded
    
    def register_engine(
        self,
        engine_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        status: Optional[EngineStatus] = None,
    ) -> bool:
        """Register a name, deriving its lifecycle from the canonical manifest.

        ``status`` overrides the derived value; pass it only when the caller knows
        something the manifest does not. Leaving it out is the normal path, and means
        a ``planned`` engine can never be registered as an available one by accident.
        """
        if engine_name in self._engines:
            logger.warning(f"Engine {engine_name} already registered, updating metadata")
        
        now = self._clock()
        rune_hash = self._compute_rune_hash(engine_name, metadata or {})
        
        rune = EngineRune(
            engine_name=engine_name,
            status=status or status_for(engine_name),
            registered_at=now,
            last_updated=now,
            metadata=metadata or {},
            rune_hash=rune_hash
        )
        
        self._engines[engine_name] = rune
        logger.info(f"Registered engine: {engine_name} ({rune.status.value})")
        return True
    
    def update_engine_status(self, engine_name: str, status: EngineStatus, 
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update the status of a registered engine."""
        if engine_name not in self._engines:
            logger.error(f"Engine {engine_name} not found in registry")
            return False
        
        rune = self._engines[engine_name]
        rune.status = status
        rune.last_updated = self._clock()
        if metadata:
            rune.metadata.update(metadata)
        rune.rune_hash = self._compute_rune_hash(engine_name, rune.metadata)
        
        logger.info(f"Updated engine {engine_name} status to {status.value}")
        return True
    
    def is_engine_registered(self, engine_name: str) -> bool:
        """Is this name addressable in the registry?

        Addressable is NOT the same as available — see ``is_engine_available``.
        """
        return engine_name in self._engines

    def is_engine_available(self, engine_name: str) -> bool:
        """May this name actually be used to produce evidence?

        False for everything the manifest does not mark ``live``. A ``planned`` engine
        stays addressable so it remains visible in the topology, but it has no
        implementation and must never be presented as available. Unknown names and
        non-engine registrations (the coordinator, test doubles, individual rune
        capabilities) are likewise unavailable.

        This is the fail-closed predicate. Prefer it over ``is_engine_registered``
        anywhere a name is about to be *used* rather than merely listed.
        """
        rune = self._engines.get(engine_name)
        return rune is not None and rune.status == EngineStatus.ACTIVE

    def available_engines(self) -> List[str]:
        """Names that could produce evidence, in registration order."""
        return [
            name for name, rune in self._engines.items()
            if rune.status == EngineStatus.ACTIVE
        ]

    def planned_engines(self) -> List[str]:
        """Addressable names with no implementation behind them."""
        return [
            name for name, rune in self._engines.items()
            if rune.status == EngineStatus.PLANNED
        ]
    
    def get_engine_rune(self, engine_name: str) -> Optional[EngineRune]:
        """Get the rune for a specific engine."""
        return self._engines.get(engine_name)
    
    def list_engines(self, status: Optional[EngineStatus] = None) -> List[str]:
        """List all engines, optionally filtered by status."""
        if status is None:
            return list(self._engines.keys())
        return [name for name, rune in self._engines.items() if rune.status == status]
    
    def get_registry_stats(self) -> RegistryStats:
        """Get statistics about the registry."""
        now = datetime.now(timezone.utc)
        today = now.date()
        
        total = len(self._engines)
        active = sum(1 for rune in self._engines.values() if rune.status == EngineStatus.ACTIVE)
        registered_today = sum(
            1 for rune in self._engines.values() 
            if datetime.fromisoformat(rune.registered_at).date() == today
        )
        
        return RegistryStats(
            total_engines=total,
            active_engines=active,
            registered_today=registered_today,
            last_updated=now.isoformat()
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the registry."""
        stats = self.get_registry_stats()
        return {
            "initialized": self._initialized,
            "stats": stats.__dict__,
            "engines": {name: rune.__dict__ for name, rune in self._engines.items()}
        }
    
    def _compute_rune_hash(self, engine_name: str, metadata: Dict[str, Any]) -> str:
        """Hash the engine's identity with the repo's canonical serializer.

        This used to hand-roll ``json.dumps(..., sort_keys=True)``. The repo already has
        a canonical authority — ``abraxas/core/canonical.py`` — and the architecture says
        not to bypass it: two serializers give two answers for the same value, and that
        difference surfaces later as provenance drift rather than as an error here.

        The hash deliberately covers identity only (name + metadata + version), never a
        timestamp, so it is stable across registrations.
        """
        from abraxas.core.canonical import canonical_json, sha256_hex

        rune_data = {
            "engine": engine_name,
            "metadata": metadata,
            "version": "1.0.0",
        }
        return sha256_hex(canonical_json(rune_data))[:32]
    
    def shutdown(self) -> None:
        """Shutdown the registry."""
        logger.info("Shutting down Yggdrasil Engine Registry")
        self._engines.clear()
        self._initialized = False