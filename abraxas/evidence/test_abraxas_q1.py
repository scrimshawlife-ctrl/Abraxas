"""ABRAXAS-Q1 Governance Qualification Test Suite

This test suite validates the ABRAXAS-Q1 qualification gates using the
deterministic fixtures defined in abraxas_q1_fixtures.yaml.

Run with: python -m pytest abraxas/evidence/test_abraxas_q1.py -v
"""

from __future__ import annotations

import yaml
import pytest
from pathlib import Path

from abraxas.evidence.contract import (
    EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep, Decision
)
from abraxas.evidence.policy import DecisionRecord
from abraxas.governance.production import (
    ProductionOrchestrator, EngineStatus, SixGateGovernor, GovernanceGate, GateResult
)


FIXTURES_PATH = Path(__file__).parent / "abraxas_q1_fixtures.yaml"


def load_fixtures() -> dict:
    """Load test fixtures from YAML."""
    with open(FIXTURES_PATH) as f:
        return yaml.safe_load(f)


class TestABRAXAS_Q1_Specification:
    """Tests for ABRAXAS-Q1 specification compliance."""

    def test_spec_file_exists(self):
        """Verify the specification document exists."""
        spec_path = Path(__file__).parent / "abraxas_governance_v1.spec.md"
        assert spec_path.exists(), "ABRAXAS-Q1 specification document missing"

    def test_spec_contains_required_sections(self):
        """Verify specification has all required gates documented."""
        spec_path = Path(__file__).parent / "abraxas_governance_v1.spec.md"
        content = spec_path.read_text()
        
        required_sections = [
            "Qualification Gates",
            "Wire-Shape Contract",
            "6-Gate Governance Schema",
            "Invariants",
            "Test Fixtures",
            "Qualification Receipt Structure",
            "Pairwise Conformance",
        ]
        
        for section in required_sections:
            assert section in content, f"Missing required section: {section}"


class TestABRAXAS_Q1_Governance:
    """Tests for 6-gate governance logic."""

    def test_six_gate_governor_exists(self):
        """SixGateGovernor should be importable and instantiable."""
        from abraxas.governance.production import ProductionArbiter
        arbiter = ProductionArbiter()
        gov = SixGateGovernor(arbiter)
        assert gov is not None
        assert len(gov.gate_weights) == 6

    def test_gate_weights_sum_to_one(self):
        """Gate weights should sum to 1.0."""
        from abraxas.governance.production import ProductionArbiter
        arbiter = ProductionArbiter()
        gov = SixGateGovernor(arbiter)
        total = sum(gov.gate_weights.values())
        assert abs(total - 1.0) < 1e-6

    def test_all_six_gates_present(self):
        """All six gates should be defined."""
        from abraxas.governance.production import ProductionArbiter
        arbiter = ProductionArbiter()
        gov = SixGateGovernor(arbiter)
        expected_gates = {
            GovernanceGate.PROVENANCE,
            GovernanceGate.FALSIFIABILITY,
            GovernanceGate.REDUNDANCY,
            GovernanceGate.RENT,
            GovernanceGate.ABLATION,
            GovernanceGate.STABILIZATION,
        }
        assert set(gov.gate_weights.keys()) == expected_gates

    def test_gate_provenance(self):
        """Test provenance gate logic."""
        from abraxas.governance.production import ProductionArbiter
        arbiter = ProductionArbiter()
        gov = SixGateGovernor(arbiter)
        
        # Create a proper DecisionRecord
        from abraxas.evidence.policy import DecisionRecord
        from abraxas.evidence.contract import Decision
        
        record = DecisionRecord(
            decision_id="test-001",
            request_id="req-001",
            evidence_ids=["e1", "e2", "e3"],
            engines_used=["e1", "e2", "e3"],
            decision=Decision.ACCEPT,
            confidence=0.85,
            verification_results=[{"passed": True}, {"passed": True}, {"passed": True}],
        )
        
        result = gov._check_provenance(record)
        assert result.gate == GovernanceGate.PROVENANCE
        assert result.passed is True
        assert result.score == 1.0

    def test_gate_falsifiability(self):
        """Test falsifiability gate logic."""
        from abraxas.governance.production import ProductionArbiter
        arbiter = ProductionArbiter()
        gov = SixGateGovernor(arbiter)
        
        from abraxas.evidence.policy import DecisionRecord
        from abraxas.evidence.contract import Decision
        
        record = DecisionRecord(
            decision_id="test-002",
            request_id="req-002",
            evidence_ids=["e1", "e2"],
            engines_used=["e1", "e2"],
            decision=Decision.VERIFY,
            confidence=0.7,
            contradictions=["c1"],
            unresolved_claims=["u1"],
        )
        
        result = gov._check_falsifiability(record)
        assert result.gate == GovernanceGate.FALSIFIABILITY
        assert result.passed is True

    def test_gate_redundancy(self):
        """Test redundancy gate logic."""
        from abraxas.governance.production import ProductionArbiter
        arbiter = ProductionArbiter()
        gov = SixGateGovernor(arbiter)
        
        from abraxas.evidence.policy import DecisionRecord
        from abraxas.evidence.contract import Decision
        
        record = DecisionRecord(
            decision_id="test-003",
            request_id="req-003",
            evidence_ids=["e1", "e2", "e3"],
            engines_used=["e1", "e2", "e3"],
            decision=Decision.ACCEPT,
            confidence=0.85,
        )
        
        result = gov._check_redundancy(record)
        assert result.gate == GovernanceGate.REDUNDANCY
        assert result.passed is True
        assert result.score == 1.0

    def test_gate_rent(self):
        """Test rent gate logic."""
        from abraxas.governance.production import ProductionArbiter
        arbiter = ProductionArbiter()
        gov = SixGateGovernor(arbiter)
        
        from abraxas.evidence.policy import DecisionRecord
        from abraxas.evidence.contract import Decision
        
        record = DecisionRecord(
            decision_id="test-004",
            request_id="req-004",
            evidence_ids=["e1", "e2", "e3"],
            engines_used=["e1", "e2", "e3"],
            decision=Decision.ACCEPT,
            confidence=0.85,
        )
        
        result = gov._check_rent(record)
        assert result.gate == GovernanceGate.RENT
        assert result.passed is True

    def test_gate_ablation(self):
        """Test ablation gate logic."""
        from abraxas.governance.production import ProductionArbiter
        arbiter = ProductionArbiter()
        gov = SixGateGovernor(arbiter)
        
        from abraxas.evidence.policy import DecisionRecord
        from abraxas.evidence.contract import Decision
        
        record = DecisionRecord(
            decision_id="test-005",
            request_id="req-005",
            evidence_ids=["e1", "e2", "e3"],
            engines_used=["e1", "e2", "e3"],
            decision=Decision.ACCEPT,
            confidence=0.8,
        )
        
        result = gov._check_ablation(record)
        assert result.gate == GovernanceGate.ABLATION
        assert result.passed is True

    def test_gate_stabilization(self):
        """Test stabilization gate logic."""
        from abraxas.governance.production import ProductionArbiter
        arbiter = ProductionArbiter()
        gov = SixGateGovernor(arbiter)
        
        from abraxas.evidence.policy import DecisionRecord
        from abraxas.evidence.contract import Decision
        
        record = DecisionRecord(
            decision_id="test-006",
            request_id="req-006",
            evidence_ids=["e1", "e2"],
            engines_used=["e1", "e2"],
            decision=Decision.ACCEPT,
            confidence=0.75,
        )
        
        result = gov._check_stabilization(record)
        assert result.gate == GovernanceGate.STABILIZATION
        assert result.passed is True
        assert result.score == 1.0

    def test_aggregate_scoring(self):
        """Test weighted aggregate scoring."""
        from abraxas.governance.production import ProductionArbiter
        arbiter = ProductionArbiter()
        gov = SixGateGovernor(arbiter)
        
        # Create mock gate results
        gate_results = [
            GateResult(gate=GovernanceGate.PROVENANCE, passed=True, score=1.0),
            GateResult(gate=GovernanceGate.FALSIFIABILITY, passed=True, score=0.8),
            GateResult(gate=GovernanceGate.REDUNDANCY, passed=True, score=1.0),
            GateResult(gate=GovernanceGate.RENT, passed=True, score=0.95),
            GateResult(gate=GovernanceGate.ABLATION, passed=True, score=0.8),
            GateResult(gate=GovernanceGate.STABILIZATION, passed=True, score=1.0),
        ]
        
        total = sum(r.score * gov.gate_weights[r.gate] for r in gate_results)
        expected = (
            1.0 * 0.20 +
            0.8 * 0.20 +
            1.0 * 0.15 +
            0.95 * 0.15 +
            0.8 * 0.15 +
            1.0 * 0.15
        )
        assert abs(total - expected) < 1e-6


class TestABRAXAS_Q1_Fixtures:
    """Tests using the deterministic Q1 fixtures."""

    @pytest.fixture(scope="class")
    def fixtures(self):
        return load_fixtures()

    def test_fixture_valid_governed_decision(self, fixtures):
        """Test valid governed decision fixture."""
        fixture = fixtures["fixture_valid_governed_decision"]
        input_data = fixture["input"]
        
        # Verify structure
        assert input_data["schema"] == "abraxas.governance.v1"
        assert input_data["version"] == "ABRAXAS_GOVERNANCE_V1"
        assert len(input_data["decision_record"]["evidence_ids"]) == 5
        assert len(input_data["decision_record"]["engines_used"]) == 5
        
        # Verify governance
        gov = input_data["governance"]
        assert gov["governed"] is True
        assert gov["aggregate_score"] > 0.9

    def test_fixture_valid_provenance_gate(self, fixtures):
        """Test valid provenance gate fixture."""
        fixture = fixtures["fixture_valid_provenance_gate"]
        input_data = fixture["input"]
        
        assert len(input_data["decision_record"]["evidence_ids"]) == 4
        assert len(input_data["decision_record"]["engines_used"]) == 4

    def test_fixture_valid_falsifiability_gate(self, fixtures):
        """Test valid falsifiability gate fixture."""
        fixture = fixtures["fixture_valid_falsifiability_gate"]
        input_data = fixture["input"]
        
        assert len(input_data["decision_record"]["contradictions"]) == 1
        assert len(input_data["decision_record"]["unresolved_claims"]) == 1
        assert input_data["decision_record"]["decision"] == "VERIFY"

    def test_fixture_valid_redundancy_gate(self, fixtures):
        """Test valid redundancy gate fixture."""
        fixture = fixtures["fixture_valid_redundancy_gate"]
        input_data = fixture["input"]
        
        assert len(input_data["decision_record"]["engines_used"]) == 5

    def test_fixture_valid_rent_gate(self, fixtures):
        """Test valid rent gate fixture."""
        fixture = fixtures["fixture_valid_rent_gate"]
        input_data = fixture["input"]
        
        assert len(input_data["decision_record"]["evidence_ids"]) == 3
        assert input_data["decision_record"]["confidence"] == 0.85

    def test_fixture_valid_ablation_gate(self, fixtures):
        """Test valid ablation gate fixture."""
        fixture = fixtures["fixture_valid_ablation_gate"]
        input_data = fixture["input"]
        
        assert len(input_data["decision_record"]["evidence_ids"]) == 3
        assert len(input_data["decision_record"]["engines_used"]) == 3

    def test_fixture_valid_stabilization_gate(self, fixtures):
        """Test valid stabilization gate fixture."""
        fixture = fixtures["fixture_valid_stabilization_gate"]
        input_data = fixture["input"]
        
        assert input_data["decision_record"]["decision"] == "ACCEPT"

    def test_fixture_invalid_ungoverned(self, fixtures):
        """Test invalid ungoverned fixture."""
        fixture = fixtures["fixture_invalid_ungoverned"]
        input_data = fixture["input"]
        
        assert len(input_data["decision_record"]["evidence_ids"]) == 1
        assert input_data["decision_record"]["decision"] == "ABSTAIN"
        assert input_data["decision_record"]["confidence"] == 0.1


class TestABRAXAS_Q1_Integration:
    """Integration tests with ProductionOrchestrator."""

    def test_governance_through_production_arbiter(self):
        """ABRAXAS governance should work through ProductionArbiter."""
        from abraxas.governance.production import ProductionOrchestrator, EngineStatus
        from abraxas.evidence.provider import EvidenceProvider
        from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput
        
        orchestrator = ProductionOrchestrator()
        
        # Register multiple engines
        class MockProvider(EvidenceProvider):
            engine_name = "mock1"
            engine_version = "1.0"
            supported_evidence_types = [EvidenceType.RELATIONAL_REASONING]
            
            def get_model_identity(self):
                return "mock"
            
            def produce_evidence(self, request_id, claim, context, budget=None):
                return EvidenceEnvelope(
                    engine=self.engine_name,
                    engine_version=self.engine_version,
                    model_identity=self.get_model_identity(),
                    request_id=request_id,
                    claim=claim,
                    candidate_outputs=[CandidateOutput(answer="Yes", confidence=0.8, reasoning_trace="mock", relation_steps=[])],
                    evidence_type=EvidenceType.RELATIONAL_REASONING,
                    confidence=0.8,
                    uncertainty=0.2,
                    provenance={"mock": True}
                )
        
        for i in range(5):
            name = f"engine{i}"
            provider = type(f"Provider{i}", (EvidenceProvider,), {
                'engine_name': name,
                'engine_version': '1.0',
                'supported_evidence_types': [EvidenceType.RELATIONAL_REASONING],
                'get_model_identity': lambda self: 'mock',
                'produce_evidence': lambda self, rid, claim, ctx, budget=None: EvidenceEnvelope(
                    engine=name,
                    engine_version='1.0',
                    model_identity='mock',
                    request_id=rid,
                    claim=claim,
                    candidate_outputs=[CandidateOutput(answer="Yes", confidence=0.8, reasoning_trace="mock", relation_steps=[])],
                    evidence_type=EvidenceType.RELATIONAL_REASONING,
                    confidence=0.8,
                    uncertainty=0.2,
                    provenance={"mock": True}
                )
            })()
            orchestrator.engine_registry.register(provider)
            orchestrator.engine_registry.update_health(name, EngineStatus.HEALTHY, latency_ms=10.0)
        
        # Create evidence from multiple engines
        envelopes = []
        for i in range(5):
            name = f"engine{i}"
            envelope = EvidenceEnvelope(
                engine=name,
                engine_version="1.0",
                model_identity="mock",
                request_id=f"test-{i}",
                claim="Test governance",
                candidate_outputs=[CandidateOutput(answer="Yes", confidence=0.8, reasoning_trace="mock", relation_steps=[])],
                evidence_type=EvidenceType.RELATIONAL_REASONING,
                confidence=0.8,
                uncertainty=0.2,
                provenance={"mock": True}
            )
            envelopes.append(envelope)
        
        # Run through arbiter
        decision = orchestrator.arbiter.arbitrate_batch(envelopes)
        
        from abraxas.evidence.contract import Decision
        assert isinstance(decision, Decision)
        
        # Create decision record and evaluate governance
        record = DecisionRecord.from_arbitration(
            request_id="test-gov-001",
            envelopes=envelopes,
            decision=decision,
            confidence=0.8,
        )
        
        governance = orchestrator.governor.evaluate(record)
        
        assert "governed" in governance
        assert "aggregate_score" in governance
        assert "gate_results" in governance
        assert len(governance["gate_results"]) == 6

    def test_cross_engine_governance(self):
        """Test governance with different engine types."""
        from abraxas.governance.production import ProductionOrchestrator, EngineStatus
        from abraxas.evidence.provider import EvidenceProvider
        from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput
        
        orchestrator = ProductionOrchestrator()
        
        # Register different engine types
        engine_configs = [
            ("athanor", EvidenceType.RELATIONAL_REASONING),
            ("hyperlex", EvidenceType.LEXICAL_SEMANTIC),
            ("semion", EvidenceType.SIGN_RELATION),
            ("noesis", EvidenceType.LATENT_STRUCTURAL),
            ("trutina", EvidenceType.CALIBRATION),
        ]
        
        for name, etype in engine_configs:
            provider = type(f"Provider{name}", (EvidenceProvider,), {
                'engine_name': name,
                'engine_version': '1.0',
                'supported_evidence_types': [etype],
                'get_model_identity': lambda self: name,
                'produce_evidence': lambda self, rid, claim, ctx, budget=None: EvidenceEnvelope(
                    engine=name,
                    engine_version='1.0',
                    model_identity=name,
                    request_id=rid,
                    claim=claim,
                    candidate_outputs=[CandidateOutput(answer="Yes", confidence=0.85, reasoning_trace="mock", relation_steps=[])],
                    evidence_type=etype,
                    confidence=0.85,
                    uncertainty=0.15,
                    provenance={"mock": True}
                )
            })()
            orchestrator.engine_registry.register(provider)
            orchestrator.engine_registry.update_health(name, EngineStatus.HEALTHY, latency_ms=10.0)
        
        # Create evidence from all 5 engines
        envelopes = []
        for name, etype in engine_configs:
            envelope = EvidenceEnvelope(
                engine=name,
                engine_version="1.0",
                model_identity=name,
                request_id=f"test-{name}",
                claim="Test cross-engine governance",
                candidate_outputs=[CandidateOutput(answer="Yes", confidence=0.85, reasoning_trace="mock", relation_steps=[])],
                evidence_type=etype,
                confidence=0.85,
                uncertainty=0.15,
                provenance={"mock": True}
            )
            envelopes.append(envelope)
        
        # Run batch arbitration
        decision = orchestrator.arbiter.arbitrate_batch(envelopes)
        
        # Create decision record
        record = DecisionRecord.from_arbitration(
            request_id="test-cross-engine",
            envelopes=envelopes,
            decision=decision,
            confidence=0.85,
        )
        
        # Evaluate governance
        governance = orchestrator.governor.evaluate(record)
        
        assert "governed" in governance
        assert "gate_results" in governance
        assert len(governance["gate_results"]) == 6
        
        # Check all gates present
        gate_names = {g["gate"] for g in governance["gate_results"]}
        expected_gates = {
            "provenance", "falsifiability", "redundancy",
            "rent", "ablation", "stabilization"
        }
        assert gate_names == expected_gates


class TestABRAXAS_Q1_Schema:
    """Tests for schema/subsystem validation."""

    def test_decision_record_schema(self):
        """DecisionRecord should have required fields."""
        record = DecisionRecord(
            decision_id="test-001",
            request_id="req-001",
            evidence_ids=["e1", "e2"],
            engines_used=["e1", "e2"],
            decision=Decision.ACCEPT,
            confidence=0.8,
        )
        
        assert record.decision_id == "test-001"
        assert record.request_id == "req-001"
        assert len(record.evidence_ids) == 2
        assert record.decision == Decision.ACCEPT

    def test_decision_record_from_arbitration(self):
        """DecisionRecord.from_arbitration should create valid record."""
        from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, Decision
        
        envelope = EvidenceEnvelope(
            engine="test",
            engine_version="1.0",
            model_identity="test",
            request_id="test-001",
            claim="Test",
            candidate_outputs=[CandidateOutput(answer="Yes", confidence=0.8, reasoning_trace="mock", relation_steps=[])],
            evidence_type=EvidenceType.RELATIONAL_REASONING,
            confidence=0.8,
            uncertainty=0.2,
        )
        
        record = DecisionRecord.from_arbitration(
            request_id="test-001",
            envelopes=[envelope],
            decision=Decision.ACCEPT,
            confidence=0.8,
        )
        
        assert record.decision_id is not None
        assert record.request_id == "test-001"
        assert record.evidence_ids == [envelope.evidence_id]
        assert record.engines_used == ["test"]
        assert record.decision == Decision.ACCEPT

    def test_gate_result_schema(self):
        """GateResult should have required fields."""
        gate_result = GateResult(
            gate=GovernanceGate.PROVENANCE,
            passed=True,
            score=1.0,
            details={"evidence_count": 5}
        )
        
        assert gate_result.gate == GovernanceGate.PROVENANCE
        assert gate_result.passed is True
        assert gate_result.score == 1.0
        assert gate_result.details["evidence_count"] == 5


# Entry point for manual execution
if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "--tb=short"])