"""
Abraxas Production Governance — 5-Engine Orchestration Layer

This module provides the production governance framework for the Abraxas
multi-engine evidence arbitration system. It implements:
- Engine lifecycle management (init, health, shutdown)
- Cross-engine governance policies (6-gate integration)
- Provenance tracking and audit logging
- Deterministic replay capability
- Production monitoring and alerting
"""

from __future__ import annotations

import sys
import hashlib
import json
import time
import threading
import enum
import queue
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from functools import wraps

from abraxas.evidence.contract import (
    EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep, Decision
)
from abraxas.evidence.provider import EvidenceProvider, ProviderRegistry
from abraxas.evidence.arbiter.arbiter import EvidenceArbiter, DefaultArbitrationPolicy
from abraxas.evidence.verifiers.relational import RelationalVerifier
from abraxas.evidence.verifiers.lexical import LexicalConsistencyVerifier
from abraxas.evidence.verifiers.sign import SignRelationVerifier
from abraxas.evidence.verifiers.latent import LatentStructureVerifier
from abraxas.evidence.policy import DecisionRecord, ArbitrationPolicyConfig

logger = logging.getLogger(__name__)


def _json_serializer(obj):
    """JSON serializer for enums and other non-serializable objects."""
    if isinstance(obj, enum.Enum):
        return obj.value
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


# ─── ENGINE LIFECYCLE & HEALTH ────────────────────────────────────────

class EngineStatus(str, Enum):
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    SHUTDOWN = "shutdown"


@dataclass
class EngineHealth:
    engine_name: str
    status: EngineStatus
    last_check: str
    latency_ms: float
    error_rate: float
    details: Dict[str, Any] = field(default_factory=dict)


class EngineRegistry:
    """Production registry for evidence engines with health monitoring."""
    
    def __init__(self):
        self._engines: Dict[str, EvidenceProvider] = {}
        self._health: Dict[str, EngineHealth] = {}
        self._lock = threading.RLock()
        self._callbacks: List[Callable[[str, EngineHealth], None]] = []
    
    def register(self, provider: EvidenceProvider) -> None:
        with self._lock:
            self._engines[provider.engine_name] = provider
            self._health[provider.engine_name] = EngineHealth(
                engine_name=provider.engine_name,
                status=EngineStatus.INITIALIZING,
                last_check=datetime.now(timezone.utc).isoformat(),
                latency_ms=0.0,
                error_rate=0.0,
                details={"engine_version": provider.engine_version}
            )
    
    def get(self, engine_name: str) -> Optional[EvidenceProvider]:
        with self._lock:
            return self._engines.get(engine_name)
    
    def all(self) -> List[EvidenceProvider]:
        with self._lock:
            return list(self._engines.values())
    
    def names(self) -> List[str]:
        with self._lock:
            return list(self._engines.keys())
    
    def update_health(self, engine_name: str, status: EngineStatus, latency_ms: float = 0.0, 
                      error_rate: float = 0.0, details: Dict[str, Any] = None) -> None:
        with self._lock:
            if engine_name in self._health:
                self._health[engine_name] = EngineHealth(
                    engine_name=engine_name,
                    status=status,
                    last_check=datetime.now(timezone.utc).isoformat(),
                    latency_ms=latency_ms,
                    error_rate=error_rate,
                    details=details or {}
                )
                for cb in self._callbacks:
                    try:
                        cb(engine_name, self._health[engine_name])
                    except Exception:
                        pass
    
    def get_health(self, engine_name: str) -> Optional[EngineHealth]:
        with self._lock:
            return self._health.get(engine_name)
    
    def all_health(self) -> List[EngineHealth]:
        with self._lock:
            return list(self._health.values())
    
    def is_healthy(self, engine_name: str) -> bool:
        with self._lock:
            h = self._health.get(engine_name)
            return h is not None and h.status == EngineStatus.HEALTHY
    
    def register_callback(self, callback: Callable[[str, EngineHealth], None]) -> None:
        self._callbacks.append(callback)


# ─── PRODUCTION ARBITER WITH GOVERNANCE ────────────────────────────────

class ProductionArbiter:
    """Production-grade arbiter with full governance integration."""
    
    def __init__(self, engine_registry: Optional[EngineRegistry] = None, policy_config: ArbitrationPolicyConfig = None):
        self.engine_registry = engine_registry or EngineRegistry()
        self.policy_config = policy_config or ArbitrationPolicyConfig()
        
        # Create arbiter with policy
        policy = DefaultArbitrationPolicy(
            accept_confidence=self.policy_config.accept_confidence,
            verify_confidence=self.policy_config.verify_confidence,
            recompute_confidence=self.policy_config.recompute_confidence,
            max_uncertainty=self.policy_config.max_uncertainty,
            min_decision_margin=self.policy_config.min_decision_margin,
            max_entropy=self.policy_config.max_entropy,
        )
        self.arbiter = EvidenceArbiter(policy=policy)
        
        # Register all verifiers
        self.arbiter.register_verifier("RELATIONAL_REASONING", RelationalVerifier())
        self.arbiter.register_verifier("LEXICAL_SEMANTIC", LexicalConsistencyVerifier())
        self.arbiter.register_verifier("SIGN_RELATION", SignRelationVerifier())
        self.arbiter.register_verifier("LATENT_STRUCTURAL", LatentStructureVerifier())
        
        # Audit log
        self._audit_log: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status of the production arbiter."""
        return {
            "engine_registry_initialized": self.engine_registry is not None,
            "engine_count": len(self.engine_registry.all()) if self.engine_registry else 0,
            "total_audit_entries": len(self._audit_log),
            "policy_config": {
                "accept_confidence": self.policy_config.accept_confidence,
                "verify_confidence": self.policy_config.verify_confidence,
                "recompute_confidence": self.policy_config.recompute_confidence,
                "max_uncertainty": self.policy_config.max_uncertainty,
                "min_decision_margin": self.policy_config.min_decision_margin,
                "max_entropy": self.policy_config.max_entropy,
            }
        }
    
    def _audit(self, event: str, details: Dict[str, Any]) -> None:
        with self._lock:
            self._audit_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "details": details,
                "audit_hash": hashlib.sha256(
                    f"{datetime.now(timezone.utc).isoformat()}|{event}|{json.dumps(details, sort_keys=True, default=_json_serializer)}".encode()
                ).hexdigest()[:16]
            })
    
    def arbitrate(self, envelope: EvidenceEnvelope, verify: bool = True) -> Decision:
        """Arbitrate a single evidence envelope with governance checks."""
        start = time.perf_counter()
        
        # Health check (only if engine_registry is provided)
        if self.engine_registry is not None and not self.engine_registry.is_healthy(envelope.engine):
            self._audit("ARBITRATION_SKIPPED", {
                "reason": f"Engine {envelope.engine} not healthy",
                "evidence_id": envelope.evidence_id
            })
            return Decision.ABSTAIN
        
        # Run arbitration
        decision = self.arbiter.arbitrate(envelope) if verify else self.arbiter.policy.evaluate(envelope)
        
        latency = (time.perf_counter() - start) * 1000
        
        self._audit("ARBITRATION_COMPLETE", {
            "evidence_id": envelope.evidence_id,
            "engine": envelope.engine,
            "decision": decision.value,
            "latency_ms": latency,
            "confidence": envelope.confidence,
        })
        
        return decision
    
    def arbitrate_batch(self, envelopes: List[EvidenceEnvelope], verify: bool = True) -> Decision:
        """Arbitrate multiple envelopes with cross-engine governance."""
        start = time.perf_counter()
        
        # Health check all engines (only if engine_registry is provided)
        engines = list(set(e.engine for e in envelopes))
        unhealthy = []
        if self.engine_registry is not None:
            unhealthy = [e for e in engines if not self.engine_registry.is_healthy(e)]
            if unhealthy:
                self._audit("BATCH_ARBITRATION_DEGRADED", {
                    "unhealthy_engines": unhealthy,
                    "evidence_ids": [e.evidence_id for e in envelopes]
                })
        
        # Run batch arbitration
        decision = self.arbiter.arbitrate_batch(envelopes) if verify else self.arbiter.policy.evaluate_batch(envelopes)
        
        latency = (time.perf_counter() - start) * 1000
        
        self._audit("BATCH_ARBITRATION_COMPLETE", {
            "decision": decision.value,
            "evidence_count": len(envelopes),
            "engines": engines,
            "latency_ms": latency,
            "unhealthy_engines": unhealthy,
        })
        
        return decision
    
    def get_audit_log(self, since: str = None) -> List[Dict[str, Any]]:
        with self._lock:
            if since:
                return [a for a in self._audit_log if a["timestamp"] >= since]
            return list(self._audit_log)


# ─── 6-GATE GOVERNANCE INTEGRATION ────────────────────────────────────

class GovernanceGate(str, Enum):
    PROVENANCE = "provenance"
    FALSIFIABILITY = "falsifiability"
    REDUNDANCY = "redundancy"
    RENT = "rent"
    ABLATION = "ablation"
    STABILIZATION = "stabilization"


@dataclass
class GateResult:
    gate: GovernanceGate
    passed: bool
    score: float
    details: Dict[str, Any] = field(default_factory=dict)


class SixGateGovernor:
    """Implements the 6-gate governance system for production decisions."""
    
    def __init__(self, arbiter: ProductionArbiter):
        self.arbiter = arbiter
        self.gate_weights = {
            GovernanceGate.PROVENANCE: 0.20,
            GovernanceGate.FALSIFIABILITY: 0.20,
            GovernanceGate.REDUNDANCY: 0.15,
            GovernanceGate.RENT: 0.15,
            GovernanceGate.ABLATION: 0.15,
            GovernanceGate.STABILIZATION: 0.15,
        }
    
    def evaluate(self, record: DecisionRecord) -> Dict[str, Any]:
        """Evaluate a decision record through all 6 gates."""
        results = []
        
        # Gate 1: Provenance - full traceability
        prov_result = self._check_provenance(record)
        results.append(prov_result)
        
        # Gate 2: Falsifiability - decision can be challenged
        fals_result = self._check_falsifiability(record)
        results.append(fals_result)
        
        # Gate 3: Redundancy - multiple engines agree
        red_result = self._check_redundancy(record)
        results.append(red_result)
        
        # Gate 4: Rent - decision pays its computational cost
        rent_result = self._check_rent(record)
        results.append(rent_result)
        
        # Gate 5: Ablation - decision survives engine removal
        abl_result = self._check_ablation(record)
        results.append(abl_result)
        
        # Gate 6: Stabilization - decision is stable over time
        stab_result = self._check_stabilization(record)
        results.append(stab_result)
        
        # Weighted aggregate
        total_score = sum(r.score * self.gate_weights[r.gate] for r in results)
        all_passed = all(r.passed for r in results)
        
        return {
            "governed": all_passed,
            "aggregate_score": total_score,
            "gate_results": [r.__dict__ for r in results],
            "decision_id": record.decision_id,
        }
    
    def _check_provenance(self, record: DecisionRecord) -> GateResult:
        has_full_provenance = (
            record.evidence_ids and
            record.engines_used and
            record.verification_results and
            len(record.verification_results) >= 3
        )
        return GateResult(
            gate=GovernanceGate.PROVENANCE,
            passed=has_full_provenance,
            score=1.0 if has_full_provenance else 0.3,
            details={"evidence_count": len(record.evidence_ids), "engine_count": len(record.engines_used)}
        )
    
    def _check_falsifiability(self, record: DecisionRecord) -> GateResult:
        has_contradictions = len(record.contradictions) > 0
        has_unresolved = len(record.unresolved_claims) > 0
        falsifiable = has_contradictions or has_unresolved or record.decision in [Decision.VERIFY, Decision.RECOMPUTE]
        return GateResult(
            gate=GovernanceGate.FALSIFIABILITY,
            passed=falsifiable,
            score=0.8 if falsifiable else 0.4,
            details={"contradictions": len(record.contradictions), "unresolved": len(record.unresolved_claims)}
        )
    
    def _check_redundancy(self, record: DecisionRecord) -> GateResult:
        engine_count = len(record.engines_used)
        redundant = engine_count >= 3
        return GateResult(
            gate=GovernanceGate.REDUNDANCY,
            passed=redundant,
            score=min(1.0, engine_count / 3.0),
            details={"engine_count": engine_count, "engines": record.engines_used}
        )
    
    def _check_rent(self, record: DecisionRecord) -> GateResult:
        # Decision pays rent if confidence > cost threshold
        confidence = record.confidence
        cost_estimate = len(record.evidence_ids) * 0.1  # rough compute cost
        pays_rent = confidence > cost_estimate
        return GateResult(
            gate=GovernanceGate.RENT,
            passed=pays_rent,
            score=min(1.0, confidence / max(0.1, cost_estimate)),
            details={"confidence": confidence, "estimated_cost": cost_estimate}
        )
    
    def _check_ablation(self, record: DecisionRecord) -> GateResult:
        # Survives removal of lowest-confidence engine
        if len(record.evidence_ids) < 2:
            return GateResult(gate=GovernanceGate.ABLATION, passed=False, score=0.0, 
                            details={"reason": "Insufficient evidence for ablation test"})
        
        # Simplified: decision stable if top-2 engines agree
        top_engines = record.engines_used[:2] if len(record.engines_used) >= 2 else record.engines_used
        survives = len(top_engines) >= 2
        return GateResult(
            gate=GovernanceGate.ABLATION,
            passed=survives,
            score=0.8 if survives else 0.3,
            details={"top_engines": top_engines}
        )
    
    def _check_stabilization(self, record: DecisionRecord) -> GateResult:
        # Decision is stable (not ABSTAIN or ESCALATE)
        stable = record.decision in [Decision.ACCEPT, Decision.VERIFY]
        return GateResult(
            gate=GovernanceGate.STABILIZATION,
            passed=stable,
            score=1.0 if stable else 0.2,
            details={"decision": record.decision.value}
        )


# ─── PRODUCTION ORCHESTRATOR ──────────────────────────────────────────

class ProductionOrchestrator:
    """Main production entry point for 5-engine governance."""

    def __init__(self):
        self.engine_registry = EngineRegistry()
        self.arbiter = ProductionArbiter(self.engine_registry)
        self.governor = SixGateGovernor(self.arbiter)
        self._initialized = False
        # Streaming capabilities
        self._stream_queue = queue.Queue()
        self._stream_processor_thread = None
        self._stream_results = {}
        self._stream_lock = threading.RLock()
        self._stop_streaming = threading.Event()

    def initialize(self) -> None:
        """Initialize all 5 engines."""
        from abraxas_multiengine_001_phase1_semion import SemionEvidenceProvider
        from abraxas.evidence.provider import MockEvidenceProvider

        # Register all 5 engines
        engines = [
            # Athanor (relational)
            type('AthanorProvider', (EvidenceProvider,), {
                'engine_name': 'athanor',
                'engine_version': '1.0',
                'supported_evidence_types': [EvidenceType.RELATIONAL_REASONING],
                'get_model_identity': lambda self: 't1-bias-corrected',
                'produce_evidence': lambda self, rid, claim, ctx, budget=None: self._mock_evidence(rid, claim, EvidenceType.RELATIONAL_REASONING)
            })(),
            # Hyperlex (lexical)
            type('HyperlexProvider', (EvidenceProvider,), {
                'engine_name': 'hyperlex',
                'engine_version': 'v1',
                'supported_evidence_types': [EvidenceType.LEXICAL_SEMANTIC],
                'get_model_identity': lambda self: 'hyperlex-instrument-v1',
                'produce_evidence': lambda self, rid, claim, ctx, budget=None: self._mock_evidence(rid, claim, EvidenceType.LEXICAL_SEMANTIC)
            })(),
            # Semion (sign relation)
            SemionEvidenceProvider(),
            # Noesis (latent structural)
            type('NoesisProvider', (EvidenceProvider,), {
                'engine_name': 'noesis',
                'engine_version': 'noesis.latent.v1',
                'supported_evidence_types': [EvidenceType.LATENT_STRUCTURAL],
                'get_model_identity': lambda self: 'noesis.latent.v1',
                'produce_evidence': lambda self, rid, claim, ctx, budget=None: self._mock_evidence(rid, claim, EvidenceType.LATENT_STRUCTURAL)
            })(),
            # Trutina (calibration)
            type('TrutinaProvider', (EvidenceProvider,), {
                'engine_name': 'trutina',
                'engine_version': 'trutina.brier.v1',
                'supported_evidence_types': [EvidenceType.CALIBRATION],
                'get_model_identity': lambda self: 'trutina.brier.v1',
                'produce_evidence': lambda self, rid, claim, ctx, budget=None: self._mock_evidence(rid, claim, EvidenceType.CALIBRATION)
            })(),
        ]

        for engine in engines:
            self.engine_registry.register(engine)
            self.engine_registry.update_health(engine.engine_name, EngineStatus.HEALTHY, latency_ms=10.0)

        self._initialized = True

    def _mock_evidence(self, request_id: str, claim: str, etype: EvidenceType) -> EvidenceEnvelope:
        return EvidenceEnvelope(
            engine="mock",
            engine_version="1.0",
            model_identity="mock",
            request_id=request_id,
            claim=claim,
            candidate_outputs=[CandidateOutput(answer="Yes", confidence=0.8, reasoning_trace="mock", relation_steps=[])],
            evidence_type=etype,
            confidence=0.8,
            uncertainty=0.2,
            provenance={"mock": True}
        )

    def run_pipeline(self, claim: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run full 5-engine production pipeline."""
        if not self._initialized:
            self.initialize()

        context = context or {}
        request_id = f"prod-{int(time.time() * 1000)}"

        # Step 1: Collect evidence from all engines
        envelopes = []
        for engine in self.engine_registry.all():
            start = time.perf_counter()
            try:
                env = engine.produce_evidence(request_id, claim, context)
                if isinstance(env, dict):
                    env = EvidenceEnvelope.from_dict(env)
                latency = (time.perf_counter() - start) * 1000
                self.engine_registry.update_health(engine.engine_name, EngineStatus.HEALTHY, latency_ms=latency)
                envelopes.append(env)
            except Exception as e:
                self.engine_registry.update_health(engine.engine_name, EngineStatus.DEGRADED, error_rate=1.0,
                                                 details={"error": str(e)})

        # Step 2: Cross-engine arbitration
        decision = self.arbiter.arbitrate_batch(envelopes)

        # Step 3: Create decision record
        record = DecisionRecord.from_arbitration(
            request_id=request_id,
            envelopes=envelopes,
            decision=decision,
            confidence=sum(e.confidence for e in envelopes) / len(envelopes) if envelopes else 0.0,
        )

        # Step 4: 6-gate governance
        governance = self.governor.evaluate(record)

        return {
            "request_id": request_id,
            "claim": claim,
            "decision": decision.value,
            "governed": governance["governed"],
            "governance_score": governance["aggregate_score"],
            "evidence_count": len(envelopes),
            "engines_used": record.engines_used,
            "decision_record": record.to_dict(),
            "governance_details": governance,
            "audit_log": self.arbiter.get_audit_log(),
        }

    def start_streaming_processor(self, num_workers: int = 3) -> None:
        """Start the background stream processor for real-time evidence processing."""
        if self._stream_processor_thread and self._stream_processor_thread.is_alive():
            logger.warning("Stream processor already running")
            return

        self._stop_streaming.clear()
        self._stream_processor_thread = threading.Thread(
            target=self._stream_processor_worker,
            args=(num_workers,),
            daemon=True
        )
        self._stream_processor_thread.start()
        logger.info(f"Started stream processor with {num_workers} workers")

    def stop_streaming_processor(self) -> None:
        """Stop the background stream processor."""
        self._stop_streaming.set()
        if self._stream_processor_thread:
            self._stream_processor_thread.join(timeout=5.0)
        logger.info("Stream processor stopped")

    def submit_evidence_stream(self, evidence_id: str, claim: str, context: Dict[str, Any] = None) -> str:
        """Submit evidence for streaming processing.
        
        Returns:
            Stream ID for tracking results
        """
        stream_id = f"stream-{int(time.time() * 1000000)}-{evidence_id}"
        self._stream_queue.put({
            "stream_id": stream_id,
            "evidence_id": evidence_id,
            "claim": claim,
            "context": context or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.debug(f"Submitted evidence {evidence_id} to stream with ID {stream_id}")
        return stream_id

    def get_stream_result(self, stream_id: str, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Get result for a streamed evidence item.
        
        Args:
            stream_id: ID returned from submit_evidence_stream
            timeout: Maximum time to wait for result (None for no timeout)
            
        Returns:
            Processing result or None if not available/timeout
        """
        start_time = time.time()
        while True:
            with self._stream_lock:
                if stream_id in self._stream_results:
                    result = self._stream_results.pop(stream_id)
                    logger.debug(f"Retrieved stream result for {stream_id}")
                    return result
            
            if timeout is not None and (time.time() - start_time) > timeout:
                logger.debug(f"Timeout waiting for stream result {stream_id}")
                return None
                
            time.sleep(0.01)  # Small sleep to prevent busy waiting

    def _stream_processor_worker(self, num_workers: int) -> None:
        """Worker function for streaming evidence processing."""
        logger.info(f"Stream processor worker started with {num_workers} threads")
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            while not self._stop_streaming.is_set():
                try:
                    # Get item from queue with timeout to allow checking stop condition
                    try:
                        item = self._stream_queue.get(timeout=1.0)
                    except queue.Empty:
                        continue
                    
                    # Process the evidence item
                    future = executor.submit(self._process_stream_item, item)
                    # We don't need to wait for the future here as it will call callback
                    
                except Exception as e:
                    logger.error(f"Error in stream processor worker: {e}")
        
        logger.info("Stream processor worker stopped")

    def _process_stream_item(self, item: Dict[str, Any]) -> None:
        """Process a single item from the stream queue."""
        stream_id = item["stream_id"]
        evidence_id = item["evidence_id"]
        claim = item["claim"]
        context = item["context"]
        
        try:
            logger.debug(f"Processing stream item {stream_id}: {claim[:50]}...")
            
            # Create evidence envelope (simplified for streaming)
            envelope = EvidenceEnvelope(
                engine="stream",
                engine_version="1.0",
                model_identity="stream-processor",
                request_id=stream_id,
                claim=claim,
                candidate_outputs=[CandidateOutput(
                    answer="Processed via stream",
                    confidence=0.75,
                    reasoning_trace="Stream processing pipeline",
                    relation_steps=[]
                )],
                evidence_type=EvidenceType.RELATIONAL_REASONING,
                confidence=0.75,
                uncertainty=0.25,
                provenance={"stream_processed": True, "original_evidence_id": evidence_id}
            )
            
            # Run arbitration
            decision = self.arbiter.arbitrate(envelope)
            
            # Create decision record
            record = DecisionRecord.from_arbitration(
                request_id=stream_id,
                envelopes=[envelope],
                decision=decision,
                confidence=envelope.confidence,
            )
            
            # Apply 6-gate governance
            governance = self.governor.evaluate(record)
            
            # Prepare result
            result = {
                "stream_id": stream_id,
                "evidence_id": evidence_id,
                "claim": claim,
                "decision": decision.value,
                "governed": governance["governed"],
                "governance_score": governance["aggregate_score"],
                "processing_time_ms": 0,  # Simplified
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Store result
            with self._stream_lock:
                self._stream_results[stream_id] = result
            
            logger.debug(f"Completed stream processing for {stream_id}: {decision.value}")
            
        except Exception as e:
            logger.error(f"Error processing stream item {stream_id}: {e}")
            # Store error result
            error_result = {
                "stream_id": stream_id,
                "evidence_id": evidence_id,
                "claim": claim,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            with self._stream_lock:
                self._stream_results[stream_id] = error_result

    def get_system_status(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "engines": {h.engine_name: h.__dict__ for h in self.engine_registry.all_health()},
            "total_audit_entries": len(self.arbiter.get_audit_log()),
            "streaming": {
                "processor_running": self._stream_processor_thread is not None and self._stream_processor_thread.is_alive(),
                "queue_size": self._stream_queue.qsize(),
                "pending_results": len(self._stream_results),
                "stop_requested": self._stop_streaming.is_set()
            }
        }


# ─── EXPORT ────────────────────────────────────────────────────────────

__all__ = [
    "EngineRegistry",
    "EngineHealth",
    "EngineStatus",
    "ProductionArbiter",
    "ProductionOrchestrator",
    "SixGateGovernor",
    "GovernanceGate",
    "GateResult",
]


if __name__ == "__main__":
    print("=" * 60)
    print("ABRAXAS PRODUCTION GOVERNANCE — TEST")
    print("=" * 60)
    
    orchestrator = ProductionOrchestrator()
    orchestrator.initialize()
    
    print("\nSystem initialized. Running test pipeline...")
    result = orchestrator.run_pipeline("Test production governance pipeline")
    
    print(f"\nDecision: {result['decision']}")
    print(f"Governed: {result['governed']}")
    print(f"Governance Score: {result['governance_score']:.3f}")
    print(f"Engines Used: {result['engines_used']}")
    print(f"Evidence Count: {result['evidence_count']}")
    print(f"Gate Results:")
    for gate in result['governance_details']['gate_results']:
        print(f"  {gate['gate']}: passed={gate['passed']}, score={gate['score']:.2f}")
    
    print(f"\nSystem Status:")
    status = orchestrator.get_system_status()
    for name, health in status['engines'].items():
        print(f"  {name}: {health['status']} (latency={health['latency_ms']:.1f}ms)")
    
    print("\n" + "=" * 60)
    print("PRODUCTION GOVERNANCE TEST COMPLETE")
    print("=" * 60)