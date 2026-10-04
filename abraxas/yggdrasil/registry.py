"""
Yggdrasil Engine Registry — Source of Truth for Engine Registration

This module implements the rune-based engine registry that serves as the
source of truth for all registered engines in the Yggdrasil system.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class EngineStatus(str, Enum):
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    FAILED = "failed"


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
    
    def __init__(self):
        self._engines: Dict[str, EngineRune] = {}
        self._initialized = False
        logger.info("Yggdrasil Engine Registry initialized")
    
    def initialize(self) -> None:
        """Initialize the registry (placeholder for future DB integration)."""
        if self._initialized:
            return
        self._initialized = True
        logger.debug("Yggdrasil Engine Registry fully initialized")
    
    def register_engine(self, engine_name: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Register an engine in the rune registry."""
        if engine_name in self._engines:
            logger.warning(f"Engine {engine_name} already registered, updating metadata")
        
        now = datetime.now(timezone.utc).isoformat()
        rune_hash = self._compute_rune_hash(engine_name, metadata or {})
        
        rune = EngineRune(
            engine_name=engine_name,
            status=EngineStatus.REGISTERED,
            registered_at=now,
            last_updated=now,
            metadata=metadata or {},
            rune_hash=rune_hash
        )
        
        self._engines[engine_name] = rune
        logger.info(f"Registered engine: {engine_name}")
        return True
    
    def update_engine_status(self, engine_name: str, status: EngineStatus, 
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update the status of a registered engine."""
        if engine_name not in self._engines:
            logger.error(f"Engine {engine_name} not found in registry")
            return False
        
        rune = self._engines[engine_name]
        rune.status = status
        rune.last_updated = datetime.now(timezone.utc).isoformat()
        if metadata:
            rune.metadata.update(metadata)
        rune.rune_hash = self._compute_rune_hash(engine_name, rune.metadata)
        
        logger.info(f"Updated engine {engine_name} status to {status.value}")
        return True
    
    def is_engine_registered(self, engine_name: str) -> bool:
        """Check if an engine is registered in the rune registry."""
        return engine_name in self._engines
    
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
        """Compute a cryptographic hash for the engine rune."""
        import hashlib
        import json
        
        # Create deterministic string for hashing
        rune_data = {
            "engine": engine_name,
            "metadata": metadata,
            "version": "1.0.0"  # Could be made configurable
        }
        
        rune_string = json.dumps(rune_data, sort_keys=True)
        return hashlib.sha256(rune_string.encode()).hexdigest()[:32]
    
    def shutdown(self) -> None:
        """Shutdown the registry."""
        logger.info("Shutting down Yggdrasil Engine Registry")
        self._engines.clear()
        self._initialized = False