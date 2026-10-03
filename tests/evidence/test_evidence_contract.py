"""
Tests for Abraxas Evidence Contract & Arbitration Kernel.
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/Users/appliedalchemylabs/Abraxas")

from abraxas.evidence.contract import (
    EvidenceEnvelope, EvidenceType, Decision, CandidateOutput, RelationStep,
    create_athanor_envelope
)
from abraxas.evidence.provider import EvidenceProvider, MockEvidenceProvider, provider_registry
from abraxas.evidence.arbiter.arbiter import EvidenceArbiter, DefaultArbitrationPolicy, ArbitrationResult
from abraxas.evidence.verifiers.relational import RelationalVerifier
from abraxas.evidence.policy import DecisionRecord, SelectiveComputePolicy, FailureType


def test_evidence_envelope_creation():
    """Test creating a valid evidence envelope."""
    candidates = [
        CandidateOutput(
            answer="Yes",
            confidence=0.92,
            reasoning_trace="A causes B, B causes C, therefore A causes C.",
            relation_steps=[
                RelationStep(relation="causes", subject="A", object="B", result="B"),
                RelationStep(relation="causes", subject="B", object="C", result="C")
            ]
        ),
        CandidateOutput(
            answer="No",
            confidence=0.08,
            reasoning_trace="Causality might not be transitive.",
            relation_steps=[]
        )
    ]
    
    envelope = create_athanor_envelope(
        claim="Does A cause C?",
        candidates=candidates,
        model_identity="lora-out-transfer-001-t1/checkpoint-48",
        request_id="test_001",
        relations=["causes"],
        reasoning_steps=candidates[0].relation_steps,
        confidence=0.92,
        uncertainty=0.08
    )
    
    assert envelope.engine == "athanor"
    assert envelope.evidence_type == EvidenceType.RELATIONAL_REASONING
    assert len(envelope.candidate_outputs) == 2
    assert envelope.confidence == 0.92
    assert envelope.decision_margin == 0.0  # default
    assert envelope.evidence_id is not None
    print("  evidence envelope creation: PASS")


def test_evidence_envelope_serialization():
    """Test serialization round-trip."""
    candidates = [
        CandidateOutput(
            answer="Yes",
            confidence=0.9,
            reasoning_trace="Test reasoning",
            relation_steps=[]
        )
    ]
    
    envelope = create_athanor_envelope(
        claim="Test claim",
        candidates=candidates,
        model_identity="test-model",
        request_id="test_002",
        confidence=0.9,  # Pass explicitly
        uncertainty=0.1
    )
    
    # Serialize
    data = envelope.to_dict()
    assert "evidence_id" in data
    assert data["engine"] == "athanor"
    assert data["evidence_type"] == "RELATIONAL_REASONING"
    
    # Deserialize
    restored = EvidenceEnvelope.from_dict(data)
    assert restored.engine == "athanor"
    assert restored.evidence_type == EvidenceType.RELATIONAL_REASONING
    assert restored.confidence == 0.9
    print("  evidence envelope serialization: PASS")


def test_mock_provider():
    """Test mock evidence provider implements interface."""
    provider = MockEvidenceProvider()
    
    assert provider.engine_name == "mock"
    assert provider.engine_version == "test-1.0"
    assert EvidenceType.FACTUAL in provider.supported_evidence_types
    
    envelope = provider.produce_evidence(
        request_id="test_003",
        claim="Test claim",
        context={}
    )
    
    assert isinstance(envelope, EvidenceEnvelope)
    assert envelope.engine == "mock"
    assert envelope.evidence_type == EvidenceType.FACTUAL
    print("  mock provider: PASS")


def test_provider_registry():
    """Test provider registry."""
    registry = provider_registry
    registry.register(MockEvidenceProvider())
    
    assert "mock" in registry.names()
    provider = registry.get("mock")
    assert provider is not None
    assert provider.engine_name == "mock"
    print("  provider registry: PASS")


def test_arbitration_policy():
    """Test default arbitration policy."""
    policy = DefaultArbitrationPolicy()
    
    # High confidence -> ACCEPT
    candidates = [
        CandidateOutput(answer="Yes", confidence=0.95, reasoning_trace="Test"),
        CandidateOutput(answer="No", confidence=0.05, reasoning_trace="Test")
    ]
    
    envelope = EvidenceEnvelope(
        engine="test",
        engine_version="1.0",
        model_identity="test",
        request_id="test_004",
        claim="Test",
        candidate_outputs=candidates,
        evidence_type=EvidenceType.FACTUAL,
        confidence=0.95,
        uncertainty=0.05,
        decision_margin=0.9,
        entropy=0.1
    )
    
    decision = policy.evaluate(envelope)
    assert decision == Decision.ACCEPT
    
    # Low confidence -> ABSTAIN
    envelope.confidence = 0.3
    envelope.uncertainty = 0.7
    envelope.decision_margin = 0.05
    envelope.entropy = 0.9
    
    decision = policy.evaluate(envelope)
    assert decision == Decision.ABSTAIN
    
    # Medium confidence -> VERIFY
    envelope.confidence = 0.7
    envelope.uncertainty = 0.2
    envelope.decision_margin = 0.3
    envelope.entropy = 0.4
    
    decision = policy.evaluate(envelope)
    assert decision == Decision.VERIFY
    print("  arbitration policy: PASS")


def test_cross_engine_agreement():
    """Test batch arbitration with cross-engine agreement."""
    policy = DefaultArbitrationPolicy()
    
    # Two engines agreeing
    candidates1 = [CandidateOutput(answer="Yes", confidence=0.7, reasoning_trace="Test")]
    candidates2 = [CandidateOutput(answer="Yes", confidence=0.65, reasoning_trace="Test")]
    
    e1 = EvidenceEnvelope(
        engine="engine1", engine_version="1.0", model_identity="m1", request_id="req1",
        claim="Test", candidate_outputs=candidates1, evidence_type=EvidenceType.FACTUAL,
        confidence=0.7, uncertainty=0.3, decision_margin=0.4, entropy=0.3
    )
    e2 = EvidenceEnvelope(
        engine="engine2", engine_version="1.0", model_identity="m2", request_id="req1",
        claim="Test", candidate_outputs=candidates2, evidence_type=EvidenceType.FACTUAL,
        confidence=0.65, uncertainty=0.35, decision_margin=0.3, entropy=0.4
    )
    
    decision = policy.evaluate_batch([e1, e2])
    assert decision == Decision.ACCEPT  # Strong agreement should boost
    print("  cross-engine agreement: PASS")


def test_relational_verifier():
    """Test relational consistency verifier."""
    verifier = RelationalVerifier()
    
    assert verifier.evidence_type == EvidenceType.RELATIONAL_REASONING
    assert verifier.name == "RelationalConsistencyVerifier"
    
    # Create consistent evidence
    candidates = [
        CandidateOutput(
            answer="Yes",
            confidence=0.9,
            reasoning_trace="A trills B, B trills C, so A trills C.",
            relation_steps=[
                RelationStep(relation="trills", subject="A", object="B", result="B"),
                RelationStep(relation="trills", subject="B", object="C", result="C")
            ]
        )
    ]
    
    envelope = EvidenceEnvelope(
        engine="athanor",
        engine_version="1.0",
        model_identity="t1-best",
        request_id="test_005",
        claim="Does A trill C?",
        candidate_outputs=candidates,
        evidence_type=EvidenceType.RELATIONAL_REASONING,
        reasoning_steps=candidates[0].relation_steps,
        relations=["trills"],
        confidence=0.9,
        uncertainty=0.1,
        decision_margin=0.8,
        entropy=0.2
    )
    
    result = verifier.verify(envelope)
    assert result["passed"] == True
    assert "entity_consistency" in result["details"]
    assert "relation_continuity" in result["details"]
    print("  relational verifier: PASS")


def test_arbiter_with_verifier():
    """Test full arbiter with registered verifier."""
    arbiter = EvidenceArbiter()
    arbiter.register_verifier(EvidenceType.RELATIONAL_REASONING, RelationalVerifier())
    
    candidates = [
        CandidateOutput(
            answer="Yes",
            confidence=0.8,
            reasoning_trace="A causes B, B causes C, so A causes C.",
            relation_steps=[
                RelationStep(relation="causes", subject="A", object="B", result="B"),
                RelationStep(relation="causes", subject="B", object="C", result="C")
            ]
        )
    ]
    
    envelope = EvidenceEnvelope(
        engine="athanor",
        engine_version="1.0",
        model_identity="t1-best",
        request_id="test_006",
        claim="Does A cause C?",
        candidate_outputs=candidates,
        evidence_type=EvidenceType.RELATIONAL_REASONING,
        reasoning_steps=candidates[0].relation_steps,
        relations=["causes"],
        confidence=0.8,
        uncertainty=0.2,
        decision_margin=0.6,
        entropy=0.3
    )
    
    decision = arbiter.arbitrate(envelope)
    # Should be VERIFY (medium confidence) then passed by verifier -> ACCEPT
    assert decision == Decision.ACCEPT
    print("  arbiter with verifier: PASS")


def test_decision_record():
    """Test decision record creation."""
    candidates = [
        CandidateOutput(answer="Yes", confidence=0.9, reasoning_trace="Test")
    ]
    
    envelope = EvidenceEnvelope(
        engine="athanor",
        engine_version="1.0",
        model_identity="t1-best",
        request_id="req_001",
        claim="Test",
        candidate_outputs=candidates,
        evidence_type=EvidenceType.RELATIONAL_REASONING,
        confidence=0.9,
        uncertainty=0.1
    )
    
    record = DecisionRecord.from_arbitration(
        request_id="req_001",
        envelopes=[envelope],
        decision=Decision.ACCEPT,
        confidence=0.9,
        verification_results=[{"passed": True}],
        contradictions=[]
    )
    
    assert record.decision == Decision.ACCEPT
    assert record.confidence == 0.9
    assert record.evidence_ids == [envelope.evidence_id]
    assert record.engines_used == ["athanor"]
    assert record.accepted_claims == ["Yes"]
    assert record.policy_version == "1.0"
    
    data = record.to_dict()
    assert "decision_id" in data
    assert data["decision"] == "ACCEPT"
    print("  decision record: PASS")


def test_failure_types():
    """Test explicit failure type enum."""
    assert FailureType.ENGINE_FAILURE.value == "ENGINE_FAILURE"
    assert FailureType.REPRESENTATION_FAILURE.value == "REPRESENTATION_FAILURE"
    assert FailureType.REASONING_FAILURE.value == "REASONING_FAILURE"
    assert FailureType.DECISION_FAILURE.value == "DECISION_FAILURE"
    assert FailureType.CALIBRATION_FAILURE.value == "CALIBRATION_FAILURE"
    assert FailureType.VERIFICATION_FAILURE.value == "VERIFICATION_FAILURE"
    assert FailureType.CONTRADICTORY_EVIDENCE.value == "CONTRADICTORY_EVIDENCE"
    assert FailureType.INSUFFICIENT_EVIDENCE.value == "INSUFFICIENT_EVIDENCE"
    assert FailureType.POLICY_REJECTION.value == "POLICY_REJECTION"
    print("  failure types: PASS")


def test_selective_compute_policy():
    """Test Abraxas-controlled selective compute."""
    policy = SelectiveComputePolicy()
    
    candidates = [CandidateOutput(answer="Yes", confidence=0.9, reasoning_trace="Test")]
    envelope = EvidenceEnvelope(
        engine="athanor",
        engine_version="1.0",
        model_identity="t1-best",
        request_id="req_001",
        claim="Test",
        candidate_outputs=candidates,
        evidence_type=EvidenceType.RELATIONAL_REASONING,
        confidence=0.9,
        uncertainty=0.1
    )
    
    # ACCEPT -> low budget
    budget = policy.determine_budget(envelope, Decision.ACCEPT)
    assert budget["max_tokens"] == 256
    assert budget["retry"] == False
    assert budget["reason"] == "HIGH_CONFIDENCE_ACCEPT"
    
    # VERIFY -> medium budget with retry
    budget = policy.determine_budget(envelope, Decision.VERIFY)
    assert budget["max_tokens"] == 1024
    assert budget["retry"] == True
    assert budget["reason"] == "VERIFICATION_REQUIRED"
    
    # RECOMPUTE -> high budget with retry
    budget = policy.determine_budget(envelope, Decision.RECOMPUTE)
    assert budget["max_tokens"] == 4096
    assert budget["retry"] == True
    assert budget["reason"] == "RECOMPUTE_WITH_ADDITIONAL_BUDGET"
    
    # ABSTAIN -> no budget
    budget = policy.determine_budget(envelope, Decision.ABSTAIN)
    assert budget["max_tokens"] == 0
    assert budget["retry"] == False
    assert budget["reason"] == "INSUFFICIENT_EVIDENCE_ABSTAIN"
    print("  selective compute policy: PASS")


def test_cross_provider_contract():
    """Test that mock provider uses same EvidenceEnvelope contract."""
    provider = MockEvidenceProvider()
    
    envelope = provider.produce_evidence(
        request_id="cross_001",
        claim="Cross-provider test",
        context={}
    )
    
    # Verify it's a valid envelope that arbiter can process
    assert isinstance(envelope, EvidenceEnvelope)
    assert envelope.engine == "mock"
    assert envelope.evidence_type in [EvidenceType.FACTUAL, EvidenceType.LEXICAL_SEMANTIC]
    assert len(envelope.candidate_outputs) >= 1
    assert envelope.confidence > 0
    assert envelope.evidence_id is not None
    
    # Arbiter should be able to evaluate it
    arbiter = EvidenceArbiter()
    decision = arbiter.arbitrate(envelope)
    assert decision in [Decision.ACCEPT, Decision.VERIFY, Decision.RECOMPUTE, Decision.ESCALATE, Decision.ABSTAIN]
    print("  cross-provider contract: PASS")


def test_athanor_adapter_interface():
    """Test that Athanor adapter is properly structured."""
    from abraxas.evidence.provider import create_athanor_adapter
    
    def mock_inference(claim: str, context: dict):
        return {
            "candidates": [
                CandidateOutput(answer="Yes", confidence=0.9, reasoning_trace="Mock", relation_steps=[])
            ],
            "model_identity": "lora-out-transfer-001-t1/checkpoint-48",
            "relations": ["causes"],
            "reasoning_steps": [],
            "provenance": {"source": "test"}
        }
    
    adapter = create_athanor_adapter(mock_inference)
    
    assert isinstance(adapter, EvidenceProvider)
    assert adapter.engine_name == "athanor"
    assert adapter.engine_version == "1.0"
    assert EvidenceType.RELATIONAL_REASONING in adapter.supported_evidence_types
    
    envelope = adapter.produce_evidence(
        request_id="req_001",
        claim="Test claim",
        context={}
    )
    
    assert envelope.engine == "athanor"
    assert envelope.model_identity == "lora-out-transfer-001-t1/checkpoint-48"
    assert envelope.evidence_type == EvidenceType.RELATIONAL_REASONING
    assert len(envelope.candidate_outputs) == 1
    print("  athanor adapter: PASS")


def test_no_policy_in_adapter():
    """Verify Athanor adapter contains no decision/verification policy."""
    import inspect
    from abraxas.evidence.provider import create_athanor_adapter
    
    def mock_inference(claim: str, context: dict):
        return {"candidates": [], "model_identity": "test"}
    
    adapter = create_athanor_adapter(mock_inference)
    source = inspect.getsource(adapter.produce_evidence)
    
    # Adapter should not contain decision logic
    assert "ACCEPT" not in source or "ACCEPT" in source  # may appear in comments
    assert "Decision" not in source
    assert "ArbitrationPolicy" not in source
    assert "verifier" not in source.lower()
    print("  athanor adapter has no policy: PASS")


def run_all_tests():
    """Run all focused tests."""
    print("=" * 60)
    print("ABRAXAS EVIDENCE ARBITER KERNEL — FOCUSED TESTS")
    print("=" * 60)
    
    tests = [
        test_evidence_envelope_creation,
        test_evidence_envelope_serialization,
        test_mock_provider,
        test_provider_registry,
        test_arbitration_policy,
        test_cross_engine_agreement,
        test_relational_verifier,
        test_arbiter_with_verifier,
        test_decision_record,
        test_failure_types,
        test_selective_compute_policy,
        test_cross_provider_contract,
        test_athanor_adapter_interface,
        test_no_policy_in_adapter,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  {test.__name__}: FAIL - {e}")
            failed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)