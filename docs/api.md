# Abraxas API Documentation

## Overview

This document provides a comprehensive guide to the Abraxas API, including evidence containers, providers, verifiers, arbiters, and governance components.

## Evidence Contract

### EvidenceEnvelope

The canonical evidence contract for all reasoning engines in Abraxas.

#### Fields

- `evidence_id` (str): Unique identifier for the evidence
- `engine` (str): Name of the engine that produced the evidence
- `engine_version` (str): Version of the engine
- `model_identity` (str): Identity of the model used
- `request_id` (str): Identifier of the request that triggered this evidence
- `claim` (str): The claim being evaluated
- `candidate_outputs` (List[CandidateOutput]): Possible answers to the claim
- `evidence_type` (EvidenceType): Type of evidence (see EvidenceType enum)
- `reasoning_steps` (List[RelationStep]): Steps in the reasoning process
- `relations` (List[str]): Relations identified in the evidence
- `intermediate_states` (List[Dict[str, Any]]): Intermediate states in reasoning
- `confidence` (float): Confidence in the evidence (0.0-1.0)
- `uncertainty` (float): Uncertainty in the evidence (0.0-1.0)
- `decision_margin` (float): Margin between top candidates
- `entropy` (float): Entropy of the candidate distribution
- `dependencies` (List[str]): Dependencies on other evidence
- `assumptions` (List[str]): Assumptions made in the evidence
- `provenance` (Dict[str, Any]): Provenance information
- `artifact_refs` (List[str]): References to artifacts
- `verification_metadata` (Dict[str, Any]): Metadata from verification processes
- `timestamp` (str): ISO timestamp when evidence was created

#### Methods

- `to_dict()` -> Dict[str, Any]: Serialize to canonical JSON
- `from_dict(cls, data: Dict[str, Any])` -> EvidenceEnvelope: Deserialize from JSON

### EvidenceType

Enumeration of evidence types supported by Abraxas:

- RELATIONAL_REASONING
- LEXICAL_SEMANTIC
- LATENT_STRUCTURAL
- CALIBRATION
- FACTUAL
- COUNTERFACTUAL
- MULTIMODAL
- SIGN_RELATION
- TEMPORAL_REASONING
- RESONANCE_ANALYSIS
- NARRATIVE_SYNTHESIS
- MULTIMODAL_INTEGRATION
- PERSISTENT_MEMORY
- YGGDRASIL_DECISION
- VIDEO_ANALYSIS

### Decision

Enumeration of possible decisions:

- ACCEPT
- VERIFY
- RECOMPUTE
- ESCALATE
- ABSTAIN
- REJECT

### CandidateOutput

A possible answer to a claim with associated confidence and reasoning.

#### Fields

- `answer` (str): The answer text
- `confidence` (float): Confidence in this answer (0.0-1.0)
- `reasoning_trace` (str): Trace of the reasoning process
- `relation_steps` (List[RelationStep]): Reasoning steps supporting this answer
- `metadata` (Dict[str, Any]): Additional metadata

### RelationStep

A step in the reasoning process relating subjects and objects.

#### Fields

- `relation` (str): The relation type (e.g., "causes", "implies")
- `subject` (str): The subject of the relation
- `object` (str): The object of the relation
- `result` (Optional[str]): The result of applying the relation
- `confidence` (float): Confidence in this step (0.0-1.0)
- `metadata` (Dict[str, Any]): Additional metadata

## Evidence Providers

### EvidenceProvider Interface

All evidence engines must implement this interface to produce evidence envelopes.

#### Properties

- `engine_name` (str): Unique name of the engine
- `engine_version` (str): Version of the engine
- `supported_evidence_types` (List[EvidenceType]): Types of evidence this engine can produce

#### Methods

- `get_model_identity()` -> str: Identity of the model used
- `produce_evidence(request_id: str, claim: str, context: Dict[str, Any], budget: Optional[Dict[str, Any]] = None)` -> EvidenceEnvelope: Produce evidence for a claim

### Built-in Providers

#### MockEvidenceProvider

A provider that returns mock evidence for testing purposes.

#### OracleAdapter

An adapter for the Oracle engine that produces NARRATIVE_SYNTHESIS evidence.

#### CypherAdapter

An adapter for the Cypher engine that produces PERSISTENT_MEMORY evidence.

## Evidence Verifiers

Verifiers assess the quality and consistency of evidence envelopes.

### Verifier Interface

All verifiers must implement this interface.

#### Properties

- `evidence_type` (str): The type of evidence this verifier handles
- `name` (str): Name of the verifier

#### Methods

- `verify(envelope: EvidenceEnvelope)` -> Dict[str, Any]: Verify the evidence and return results

### Built-in Verifiers

#### RelationalVerifier

Verifies relational reasoning evidence (EvidenceType.RELATIONAL_REASONING).

#### LexicalConsistencyVerifier

Verifies lexical semantic evidence (EvidenceType.LEXICAL_SEMANTIC).

#### SignRelationVerifier

Verifies sign relation evidence (EvidenceType.SIGN_RELATION).

#### LatentStructureVerifier

Verifies latent structural evidence (EvidenceType.LATENT_STRUCTURAL).

## Evidence Arbiter

The arbiter combines evidence from multiple engines and applies verification to reach a decision.

### EvidenceArbiter

Combines evidence from multiple engines and applies verification policies.

#### Constructor

- `EvidenceArbiter(policy: DefaultArbitrationPolicy)`: Create an arbiter with a policy

#### Methods

- `register_verifier(evidence_type: str, verifier: Verifier)`: Register a verifier for an evidence type
- `arbitrate(envelope: EvidenceEnvelope, verify: bool = True)` -> Decision: Arbitrate a single evidence envelope
- `arbitrate_batch(envelopes: List[EvidenceEnvelope], verify: bool = True)` -> Decision: Arbitrate a batch of evidence envelopes

### DefaultArbitrationPolicy

Default policy for evidence arbitration with configurable thresholds.

#### Configuration Parameters

- `accept_confidence` (float): Threshold for automatic acceptance (default: 0.85)
- `verify_confidence` (float): Threshold for requiring verification (default: 0.60)
- `recompute_confidence` (float): Threshold for requiring recomputation (default: 0.40)
- `max_uncertainty` (float): Maximum allowed uncertainty (default: 0.30)
- `min_decision_margin` (float): Minimum decision margin (default: 0.15)
- `max_entropy` (float): Maximum allowed entropy (default: 0.70)
- `min_entity_consistency` (float): Minimum entity consistency (default: 0.70)
- `min_relation_continuity` (float): Minimum relation continuity (default: 0.70)
- `min_composition_order` (float): Minimum composition order (default: 0.70)
- `contradiction_escalates` (bool): Whether contradictions trigger escalation (default: True)
- `cross_engine_agreement_threshold` (float): Threshold for cross-engine agreement (default: 0.80)
- `require_verification_for_depth` (int): Depth at which verification is required (default: 6)

## Governance Components

### ProductionArbiter

Production-grade arbiter with full governance integration.

#### Features

- Engine lifecycle management
- Cross-engine governance policies (6-gate integration)
- Provenance tracking and audit logging
- Deterministic replay capability
- Production monitoring and alerting

#### Key Methods

- `arbitrate(envelope: EvidenceEnvelope, verify: bool = True)` -> Decision: Arbitrate with governance checks
- `arbitrate_batch(envelopes: List[EvidenceEnvelope], verify: bool = True)` -> Decision: Batch arbitration with governance
- `get_system_status()` -> Dict[str, Any]: Get system status
- `get_audit_log(since: str = None)` -> List[Dict[str, Any]]: Get audit log entries

### ProductionOrchestrator

Main production entry point for 5-engine governance with streaming capabilities.

#### Features

- Engine lifecycle management for 5 core engines (Athanor, Hyperlex, Semion, Noesis, Trutina)
- 6-gate governance integration
- Real-time streaming processing capabilities
- System status monitoring

#### Key Methods

- `initialize()`: Initialize all engines
- `run_pipeline(claim: str, context: Dict[str, Any] = None)` -> Dict[str, Any]: Run full 5-engine pipeline
- `start_streaming_processor(num_workers: int = 3)`: Start background stream processor
- `stop_streaming_processor()`: Stop background stream processor
- `submit_evidence_stream(evidence_id: str, claim: str, context: Dict[str, Any] = None)` -> str: Submit evidence for streaming
- `get_stream_result(stream_id: str, timeout: Optional[float] = None)` -> Optional[Dict[str, Any]]: Get stream result
- `get_system_status()` -> Dict[str, Any]: Get system status including streaming info

### SixGateGovernor

Implements the 6-gate governance system for production decisions.

#### Gates

1. **Provenance**: Full traceability of evidence
2. **Falsifiability**: Decision can be challenged
3. **Redundancy**: Multiple engines agree
4. **Rent**: Decision pays its computational cost
5. **Ablation**: Decision survives engine removal
6. **Stabilization**: Decision is stable over time

#### Gate Results

Each gate returns:
- `gate` (GovernanceGate): The gate being evaluated
- `passed` (bool): Whether the gate passed
- `score` (float): Score from 0.0 to 1.0
- `details` (Dict[str, Any]): Gate-specific details

#### Overall Result

- `governed` (bool): Whether all gates passed
- `aggregate_score` (float): Weighted average of gate scores
- `gate_results` (List[Dict]): Results for each gate
- `decision_id` (str): ID of the decision record

## Memory Layer

### CypherMemoryLayer

Persistent memory layer for storing evidence envelopes and decisions.

#### Features

- File-based storage with optional Timechain integration
- JSON serialization with enum handling
- Concurrent access safety
- Backup and recovery capabilities

#### Key Methods

- `initialize()`: Initialize the memory layer
- `store_evidence(envelope: Any)` -> str: Store an evidence envelope
- `store_decision(evidence_id: str, decision: Any)` -> str: Store a decision
- `retrieve_evidence(record_id: str)` -> Optional[Dict[str, Any]]: Retrieve evidence
- `retrieve_decision(evidence_id: str)` -> Optional[Dict[str, Any]]: Retrieve decision
- `list_records(record_type: Optional[str] = None)` -> List[str]: List record IDs
- `get_status()` -> Dict[str, Any]: Get memory layer status
- `shutdown()`: Shutdown the memory layer

#### Timechain Integration

The memory layer can optionally integrate with Timechain for persistent, tamper-evident storage.

To enable Timechain integration:
1. Install the Timechain package
2. Create a TimechainConfig with enabled=True
3. Pass the config to CypherMemoryLayer constructor

## Yggdrasil Coordinator

Central decision layer for the Abraxas multi-engine system.

#### Features

- Rune Registry (source of truth for engines)
- Ritual Engine (drives execution pipeline)
- Topology Router (audit → hash → validate → route)
- Evidence Collector interface
- 6-gate governance integration
- Cypher persistent memory layer

#### Key Methods

- `arbitrate_evidence(envelope: EvidenceEnvelope)` -> Decision: Arbitrate evidence through the decision layer
- `arbitrate_batch(envelopes: List[EvidenceEnvelope])` -> Decision: Arbitrate a batch of evidence
- `get_system_status()` -> Dict[str, Any]: Get status of all subsystems
- `shutdown()`: Shutdown all subsystems

## Usage Examples

### Basic Evidence Creation and Arbitration

```python
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep
from abraxas.evidence.provider import EvidenceProvider
from abraxas.evidence.arbiter.arbiter import EvidenceArbiter, DefaultArbitrationPolicy
from abraxas.evidence.verifiers.relational import RelationalVerifier
from abraxas.governance.production import ProductionArbiter

# Create arbiter with verifiers
policy = DefaultArbitrationPolicy()
arbiter = EvidenceArbiter(policy=policy)
arbiter.register_verifier("RELATIONAL_REASONING", RelationalVerifier())

# Create evidence envelope
envelope = EvidenceEnvelope(
    engine="test_engine",
    engine_version="1.0",
    model_identity="test_model",
    request_id="req-001",
    claim="The sky is blue due to Rayleigh scattering",
    candidate_outputs=[CandidateOutput(
        answer="Yes",
        confidence=0.95,
        reasoning_trace="Scientific explanation of Rayleigh scattering",
        relation_steps=[RelationStep(
            relation="causes",
            subject="Rayleigh scattering",
            object="blue sky appearance",
            result="scattering of shorter wavelengths",
            confidence=0.9
        )]
    )],
    evidence_type=EvidenceType.RELATIONAL_REASONING,
    confidence=0.95,
    uncertainty=0.05,
    provenance={"source": "scientific_consensus"}
)

# Arbitrate the evidence
decision = arbiter.arbitrate(envelope)
print(f"Decision: {decision}")
```

### Using the Production Orchestrator

```python
from abraxas.governance.production import ProductionOrchestrator

# Create and initialize orchestrator
orchestrator = ProductionOrchestrator()
orchestrator.initialize()

# Run a claim through the full pipeline
result = orchestrator.run_pipeline(
    claim="Is machine learning effective for pattern recognition?",
    context={
        "domain": "computer_science",
        "urgency": "medium",
        "required_confidence": 0.8
    }
)

print(f"Decision: {result['decision']}")
print(f"Governed: {result['governed']}")
print(f"Governance Score: {result['governance_score']:.3f}")
print(f"Engines Used: {result['engines_used']}")
```

### Using Streaming Capabilities

```python
from abraxas.governance.production import ProductionOrchestrator
import time

# Create orchestrator and start streaming processor
orchestrator = ProductionOrchestrator()
orchestrator.initialize()
orchestrator.start_streaming_processor(num_workers=3)

# Submit evidence for streaming processing
stream_id1 = orchestrator.submit_evidence_stream(
    "evidence-001",
    "What is the capital of France?",
    {"priority": "high", "domain": "geography"}
)

stream_id2 = orchestrator.submit_evidence_stream(
    "evidence-002",
    "Explain the theory of relativity",
    {"priority": "medium", "domain": "physics"}
)

# Wait for processing and retrieve results
time.sleep(2)  # Allow time for processing

result1 = orchestrator.get_stream_result(stream_id1, timeout=5.0)
result2 = orchestrator.get_stream_result(stream_id2, timeout=5.0)

print(f"Stream 1 Result: {result1}")
print(f"Stream 2 Result: {result2}")

# Stop the streaming processor when done
orchestrator.stop_streaming_processor()
```

## Error Handling

All Abraxas components are designed to handle errors gracefully:

- Validation errors return informative messages rather than crashing
- Storage failures are logged and handled without data loss
- Engine failures in the orchestrator are isolated and don't halt processing
- Verifier failures are caught and don't prevent arbitration from completing
- Network issues in distributed components trigger retry mechanisms with exponential backoff

## Performance Characteristics

Abraxas is designed for high-performance, low-latency operation:

- Evidence creation: ~0.1ms per envelope on modern hardware
- Serialization/deserialization: ~0.05ms per operation
- Full orchestrator pipeline: ~10-50ms depending on engine complexity
- Memory operations: ~0.2ms for store/retrieve operations
- Streaming throughput: ~1000 events/second per worker thread

See the benchmarks/benchmark_suite.py for detailed performance measurements.

## Extending Abraxas

### Adding New Evidence Types

1. Add a new value to the EvidenceType enum in abraxas/evidence/contract.py
2. Implement any necessary changes to evidence processing pipelines
3. Update verification logic if needed
4. Add appropriate handling in governance components

### Adding New Verifiers

1. Create a class implementing the Verifier interface
2. Register the verifier with the arbiter using `arbiter.register_verifier()`
3. Ensure the verifier handles its evidence_type correctly
4. Add unit tests for the verifier

### Adding New Providers

1. Create a class implementing the EvidenceProvider interface
2. Register the provider with the engine registry
3. Ensure the provider produces valid EvidenceEnvelope objects
4. Add integration tests for the provider

## Security Considerations

- All inputs are validated and sanitized where appropriate
- No hardcoded credentials or secrets in the codebase
- Role-based access control can be implemented at the service layer
- Audit trails provide complete provenance for all decisions
- Memory encryption options available for sensitive deployments
- Regular security audits and penetration testing recommended

## Conclusion

Abraxas provides a robust, extensible framework for multi-engine evidence arbitration with strong governance guarantees. The modular design allows for easy extension and customization while maintaining strict contracts between components.

For more information, see the source code and additional documentation in the docs/ directory.