"""
Yggdrasil Coordinator — Central Decision Layer for Abraxas

This module implements Yggdrasil as the central decision layer with:
- Rune Registry (source of truth)
- Ritual Engine (drives execution pipeline)
- Topology Router (audit → hash → validate → route)
- Evidence Collector interface
- 6-gate governance integration
- Cypher persistent memory layer
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, Decision
from abraxas.evidence.provider import EvidenceProvider
from abraxas.governance.production import ProductionOrchestrator, ProductionArbiter
from abraxas.evidence.arbiter.arbiter import EvidenceArbiter

logger = logging.getLogger(__name__)


@dataclass
class YggdrasilConfig:
    """Configuration for Yggdrasil central decision layer."""
    inference_authority: bool = True
    governance_enabled: bool = True
    memory_enabled: bool = True
    rune_registry_enabled: bool = True
    ritual_engine_enabled: bool = True
    topology_router_enabled: bool = True


class YggdrasilCoordinator:
    """Yggdrasil as central decision layer for Abraxas multi-engine system."""

    def __init__(self, config: Optional[YggdrasilConfig] = None):
        self.config = config or YggdrasilConfig()
        self._initialized = False
        
        # Initialize subsystems
        if self.config.rune_registry_enabled:
            from .registry import YggdrasilEngineRegistry
            self.rune_registry = YggdrasilEngineRegistry()
        
        if self.config.ritual_engine_enabled:
            from .ritual import RitualEngine
            self.ritual_engine = RitualEngine()
        
        if self.config.topology_router_enabled:
            from .topology import TopologyRouter
            self.topology_router = TopologyRouter()
        
        if self.config.memory_enabled:
            from .memory import CypherMemoryLayer
            self.memory_layer = CypherMemoryLayer()
        
        # Production arbiter for evidence arbitration
        self.production_arbiter = ProductionArbiter()
        
        logger.info("Yggdrasil Coordinator initialized")
    
    def initialize(self) -> None:
        """Initialize all Yggdrasil subsystems."""
        if self._initialized:
            return
        
        try:
            # Initialize rune registry with known engines
            if self.config.rune_registry_enabled:
                self._register_default_engines()
            
            # Initialize memory layer
            if self.config.memory_enabled:
                self.memory_layer.initialize()
            
            self._initialized = True
            logger.info("Yggdrasil subsystems initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Yggdrasil subsystems: {e}")
            # Don't set _initialized to True on failure
            raise
    
    def _register_default_engines(self) -> None:
        """Register the default set of engines in the rune registry.

        The list comes from abraxas.engines.manifest, the single source of truth.
        It previously lived here as a literal that disagreed with both the
        production registry and the engines that actually exist.
        """
        from abraxas.engines.manifest import registrable_names

        default_engines = list(registrable_names())
        
        for engine_name in default_engines:
            self.rune_registry.register_engine(engine_name, {
                "status": "registered",
                "registered_at": datetime.now(timezone.utc).isoformat()
            })
    
    def arbitrate_evidence(self, envelope: EvidenceEnvelope) -> Decision:
        """Arbitrate evidence through the full Yggdrasil decision layer."""
        if not self._initialized:
            self.initialize()
        
        logger.debug(f"Yggdrasil arbitrating evidence: {envelope.claim[:50]}...")
        
        # Step 1: Check rune registry for engine validity
        if self.config.rune_registry_enabled:
            if not self.rune_registry.is_engine_registered(envelope.engine):
                logger.warning(f"Engine {envelope.engine} not registered in rune registry")
                # Could reject or use fallback
        
        # Step 2: Execute governance ritual
        if self.config.ritual_engine_enabled:
            ritual_result = self.ritual_engine.execute_ritual("evidence_arbitration", {
                "envelope": envelope,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            if not ritual_result.get("success", False):
                logger.warning(f"Ritual execution failed: {ritual_result.get('error')}")
        
        # Step 3: Route through topology (audit → hash → validate → route)
        if self.config.topology_router_enabled:
            route_result = self.topology_router.route_evidence(envelope)
            if not route_result.get("valid", True):
                logger.warning(f"Topology routing invalid: {route_result.get('reason')}")
        
        # Step 4: Store in persistent memory (Cypher)
        if self.config.memory_enabled:
            self.memory_layer.store_evidence(envelope)
        
        # Step 5: Arbitrate with production arbiter (includes 6-gate governance)
        decision = self.production_arbiter.arbitrate(envelope)
        
        # Step 6: Record decision in memory
        if self.config.memory_enabled:
            self.memory_layer.store_decision(envelope.evidence_id, decision)
        
        logger.debug(f"Yggdrasil decision: {decision.value}")
        return decision
    
    def arbitrate_batch(self, envelopes: List[EvidenceEnvelope]) -> Decision:
        """Arbitrate a batch of evidence envelopes."""
        if not self._initialized:
            self.initialize()
        
        logger.debug(f"Yggdrasil batch arbitrating {len(envelopes)} envelopes")
        
        # Process each envelope through the decision layer
        decisions = []
        for envelope in envelopes:
            decision = self.arbitrate_evidence(envelope)
            decisions.append(decision)
        
        # For batch, we return the consensus decision (simplified)
        # In practice, this would be more sophisticated
        accept_count = sum(1 for d in decisions if d == Decision.ACCEPT)
        reject_count = sum(1 for d in decisions if d == Decision.REJECT)
        
        if accept_count > reject_count:
            return Decision.ACCEPT
        elif reject_count > accept_count:
            return Decision.REJECT
        else:
            return Decision.VERIFY  # Tie goes to verify
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all Yggdrasil subsystems."""
        status = {
            "coordinator": "initialized" if self._initialized else "not_initialized",
            "config": self.config.__dict__,
        }
        
        if self.config.rune_registry_enabled:
            status["rune_registry"] = self.rune_registry.get_status()
        
        if self.config.ritual_engine_enabled:
            status["ritual_engine"] = self.ritual_engine.get_status()
        
        if self.config.topology_router_enabled:
            status["topology_router"] = self.topology_router.get_status()
        
        if self.config.memory_enabled:
            status["memory_layer"] = self.memory_layer.get_status()
        
        status["production_arbiter"] = self.production_arbiter.get_system_status()
        
        return status
    
    def shutdown(self) -> None:
        """Shutdown all Yggdrasil subsystems."""
        logger.info("Shutting down Yggdrasil Coordinator")
        
        if self.config.memory_enabled:
            self.memory_layer.shutdown()
        
        # Other subsystems would shutdown here
        
        self._initialized = False


# Global coordinator instance
coordinator = YggdrasilCoordinator()
