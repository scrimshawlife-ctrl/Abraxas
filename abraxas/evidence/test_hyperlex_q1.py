"""HYPERLEX-Q1 Qualification Test Suite

This test suite validates the HYPERLEX-Q1 qualification gates using the
deterministic fixtures defined in hyperlex_q1_fixtures.yaml.

Run with: python -m pytest abraxas/evidence/test_hyperlex_q1.py -v
"""

from __future__ import annotations

import os
import yaml
import pytest
from pathlib import Path

from abraxas.evidence.hyperlex_instrument import (
    HyperlexAuthorityError,
    adapt_observation,
    assert_not_authoritative,
    instrument_enabled,
    observe_text,
    promote_to_canonical_state,
)


FIXTURES_PATH = Path(__file__).parent / "hyperlex_q1_fixtures.yaml"


def load_fixtures() -> dict:
    """Load test fixtures from YAML."""
    with open(FIXTURES_PATH) as f:
        return yaml.safe_load(f)


class TestHYPERLEX_Q1_Specification:
    """Tests for HYPERLEX-Q1 specification compliance."""

    def test_spec_file_exists(self):
        """Verify the specification document exists."""
        spec_path = Path(__file__).parent / "hyperlex_instrument_v1.spec.md"
        assert spec_path.exists(), "HYPERLEX-Q1 specification document missing"

    def test_spec_contains_required_sections(self):
        """Verify specification has all required gates documented."""
        spec_path = Path(__file__).parent / "hyperlex_instrument_v1.spec.md"
        content = spec_path.read_text()
        
        required_sections = [
            "Qualification Gates",
            "Wire-Shape Contract",
            "Invariants",
            "Test Fixtures",
            "Qualification Receipt Structure",
            "Pairwise Conformance",
        ]
        
        for section in required_sections:
            assert section in content, f"Missing required section: {section}"


class TestHYPERLEX_Q1_Fixtures:
    """Tests using the deterministic Q1 fixtures."""

    @pytest.fixture(scope="class")
    @classmethod
    def fixtures(self):
        return load_fixtures()

    def test_fixture_minimal_valid(self, fixtures):
        """Test minimal valid observation adapts correctly."""
        fixture = fixtures["fixture_minimal_valid"]
        input_obs = fixture["input"]
        expected = fixture["expected_output"]
        
        result = adapt_observation(input_obs, kind="SHADOW_SIGNAL")
        
        # Check critical invariants
        assert result["schema"] == expected["schema"]
        assert result["kind"] == expected["kind"]
        assert result["source"] == expected["source"]
        assert result["authority"] == expected["authority"]
        assert result["semantic_truth"] == expected["semantic_truth"]
        assert result["may_authorize"] == expected["may_authorize"]
        assert result["may_mutate_governing_state"] == expected["may_mutate_governing_state"]
        assert result["valid_for_forecast"] == expected["valid_for_forecast"]
        assert result["influence_policy"] == expected["influence_policy"]
        assert result["lane"] == expected["lane"]
        assert result["instrument_version"] == expected["instrument_version"]
        assert result["ontology_version"] == expected["ontology_version"]
        assert result["contract_version"] == expected["contract_version"]
        assert result["evidence"]["present"] == expected["evidence"]["present"]
        assert result["evidence"]["score"] == expected["evidence"]["score"]
        assert result["evidence"]["abstain"] == expected["evidence"]["abstain"]
        assert len(result["candidates"]) == len(expected["candidates"])
        
        # Verify assert_not_authoritative passes
        assert_not_authoritative(result)

    def test_fixture_abstain(self, fixtures):
        """Test abstain observation adapts correctly."""
        fixture = fixtures["fixture_abstain"]
        input_obs = fixture["input"]
        expected = fixture["expected_output"]
        
        result = adapt_observation(input_obs, kind="SHADOW_SIGNAL")
        
        assert result["evidence"]["present"] == expected["evidence"]["present"]
        assert result["evidence"]["score"] == expected["evidence"]["score"]
        assert result["evidence"]["abstain"] == expected["evidence"]["abstain"]
        assert result["evidence"]["reason"] == expected["evidence"]["reason"]
        assert result["candidates"] == expected["candidates"]
        
        assert_not_authoritative(result)

    def test_fixture_multi_candidate(self, fixtures):
        """Test multi-candidate observation adapts correctly."""
        fixture = fixtures["fixture_multi_candidate"]
        input_obs = fixture["input"]
        expected = fixture["expected_output"]
        
        result = adapt_observation(input_obs, kind="SHADOW_SIGNAL")
        
        assert len(result["candidates"]) == 3
        assert result["candidates"][0]["concept_id"] == "domain.crypto"
        assert result["candidates"][1]["concept_id"] == "archetype.pump_fun"
        assert result["candidates"][2]["concept_id"] == "domain.defi"
        
        # All candidates must be advisory
        for c in result["candidates"]:
            assert c["advisory"] is True
            assert c["status"] == "advisory"
        
        assert_not_authoritative(result)

    def test_fixture_shadow_signal_role(self, fixtures):
        """Test SHADOW_SIGNAL role is preserved."""
        fixture = fixtures["fixture_shadow_signal_role"]
        input_obs = fixture["input"]
        
        result = adapt_observation(input_obs, kind="SHADOW_SIGNAL")
        
        assert result["kind"] == "SHADOW_SIGNAL"
        assert_not_authoritative(result)


class TestHYPERLEX_Q1_AuthorityBoundary:
    """Tests for authority boundary enforcement (must reject)."""

    @pytest.fixture(scope="class")
    @classmethod
    def fixtures(self):
        return load_fixtures()

    def _base_obs(self):
        """Get a valid base observation."""
        return load_fixtures()["fixture_minimal_valid"]["input"]

    def test_semantic_truth_true_rejected(self, fixtures):
        """semantic_truth=true must be rejected at boundary."""
        fixture = fixtures["fixture_semantic_truth_true"]
        obs = self._base_obs()
        obs["authority"]["semantic_truth"] = True
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            adapt_observation(obs, kind="SHADOW_SIGNAL")
        assert "semantic_truth" in str(exc.value).lower()

    def test_non_advisory_candidate_rejected(self, fixtures):
        """Non-advisory candidate must be rejected."""
        fixture = fixtures["fixture_non_advisory_candidate"]
        obs = self._base_obs()
        obs["candidates"][0]["advisory"] = False
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            adapt_observation(obs, kind="SHADOW_SIGNAL")
        assert "non-advisory candidate" in str(exc.value).lower()

    @pytest.mark.parametrize("forbidden_kind", [
        "CANONICAL_STATE",
        "GOLD",
        "FINAL_INTERPRETATION",
        "AUTHORIZATION",
    ])
    def test_authoritative_kind_rejected(self, forbidden_kind):
        """Authoritative kinds must be rejected (not in ALLOWED_KINDS)."""
        obs = self._base_obs()
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            adapt_observation(obs, kind=forbidden_kind)
        # The adapter checks ALLOWED_KINDS first, so error message is about allowed kinds
        assert "kind must be one of" in str(exc.value).lower()
        assert forbidden_kind.lower() in str(exc.value).lower()

    def test_authority_kind_not_advisory_rejected(self):
        """authority.kind != advisory must be rejected."""
        obs = self._base_obs()
        obs["authority"]["kind"] = "authoritative"
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            adapt_observation(obs, kind="SHADOW_SIGNAL")
        assert "authority must be advisory" in str(exc.value).lower()


class TestHYPERLEX_Q1_AssertNotAuthoritative:
    """Tests for assert_not_authoritative enforcement."""

    def _valid_adapter_output(self):
        """Get a valid adapter output."""
        obs = load_fixtures()["fixture_minimal_valid"]["input"]
        return adapt_observation(obs, kind="SHADOW_SIGNAL")

    def test_rejects_valid_for_forecast_true(self):
        """Must reject valid_for_forecast=true."""
        evidence = self._valid_adapter_output()
        evidence = dict(evidence, valid_for_forecast=True)
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            assert_not_authoritative(evidence)
        assert "valid_for_forecast" in str(exc.value).lower()

    def test_rejects_authority_not_advisory(self):
        """Must reject authority != advisory."""
        evidence = self._valid_adapter_output()
        evidence = dict(evidence, authority="authoritative")
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            assert_not_authoritative(evidence)
        assert "authority must be advisory" in str(exc.value).lower()

    def test_rejects_semantic_truth_true(self):
        """Must reject semantic_truth=true."""
        evidence = self._valid_adapter_output()
        evidence = dict(evidence, semantic_truth=True)
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            assert_not_authoritative(evidence)
        assert "semantic_truth" in str(exc.value).lower()

    def test_rejects_may_authorize_true(self):
        """Must reject may_authorize=true."""
        evidence = self._valid_adapter_output()
        evidence = dict(evidence, may_authorize=True)
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            assert_not_authoritative(evidence)
        assert "may_authorize" in str(exc.value).lower()

    def test_rejects_may_mutate_true(self):
        """Must reject may_mutate_governing_state=true."""
        evidence = self._valid_adapter_output()
        evidence = dict(evidence, may_mutate_governing_state=True)
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            assert_not_authoritative(evidence)
        assert "may_mutate_governing_state" in str(exc.value).lower()

    def test_rejects_influence_policy_not_none(self):
        """Must reject influence_policy != NONE."""
        evidence = self._valid_adapter_output()
        evidence = dict(evidence, influence_policy="INFLUENCE")
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            assert_not_authoritative(evidence)
        assert "influence_policy" in str(exc.value).lower()

    @pytest.mark.parametrize("bad_kind", [
        "CANONICAL_STATE", "GOLD", "FINAL_INTERPRETATION", "AUTHORIZATION"
    ])
    def test_rejects_authoritative_kind(self, bad_kind):
        """Must reject authoritative kinds."""
        evidence = self._valid_adapter_output()
        evidence = dict(evidence, kind=bad_kind)
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            assert_not_authoritative(evidence)
        assert "kind must not be authoritative" in str(exc.value).lower()


class TestHYPERLEX_Q1_PromotionBlocked:
    """Tests that promotion to canonical state is always blocked."""

    def _valid_adapter_output(self):
        obs = load_fixtures()["fixture_minimal_valid"]["input"]
        return adapt_observation(obs, kind="SHADOW_SIGNAL")

    def test_promote_to_canonical_always_raises(self):
        """promote_to_canonical_state must always raise."""
        evidence = self._valid_adapter_output()
        
        with pytest.raises(HyperlexAuthorityError) as exc:
            promote_to_canonical_state(evidence)
        assert "cannot become CANONICAL_STATE" in str(exc.value)


class TestHYPERLEX_Q1_Integration:
    """Integration tests with ProductionArbiter (using mock engines)."""

    def test_evidence_through_production_arbiter(self):
        """HYPERLEX evidence should arbitrate through ProductionArbiter."""
        from abraxas.governance.production import ProductionOrchestrator, EngineStatus
        
        orchestrator = ProductionOrchestrator()
        # Don't call initialize() since it tries to import semion adapter
        # Manually register a hyperlex-like engine
        from abraxas.evidence.provider import EvidenceProvider
        from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput
        
        class HyperlexProvider(EvidenceProvider):
            engine_name = "hyperlex"
            engine_version = "v1"
            supported_evidence_types = [EvidenceType.LEXICAL_SEMANTIC]
            
            def get_model_identity(self):
                return "hyperlex-instrument-v1"
            
            def produce_evidence(self, request_id, claim, context, budget=None):
                return EvidenceEnvelope(
                    engine=self.engine_name,
                    engine_version=self.engine_version,
                    model_identity=self.get_model_identity(),
                    request_id=request_id,
                    claim=claim,
                    candidate_outputs=[
                        CandidateOutput(
                            answer="domain.crypto",
                            confidence=0.8,
                            reasoning_trace="Hyperlex instrumental observation",
                            relation_steps=[]
                        )
                    ],
                    evidence_type=EvidenceType.LEXICAL_SEMANTIC,
                    confidence=0.8,
                    uncertainty=0.2,
                    provenance={
                        "source": "hyperlex",
                        "authority": "advisory",
                        "semantic_truth": False,
                        "influence_policy": "NONE",
                        "valid_for_forecast": False,
                        "lane": "shadow",
                    }
                )
        
        orchestrator.engine_registry.register(HyperlexProvider())
        orchestrator.engine_registry.update_health("hyperlex", EngineStatus.HEALTHY, latency_ms=10.0)
        
        # Create hyperlex-like evidence
        envelope = EvidenceEnvelope(
            engine="hyperlex",
            engine_version="v1",
            model_identity="hyperlex-instrument-v1",
            request_id="test-q1-001",
            claim="Test hyperlex integration",
            candidate_outputs=[
                CandidateOutput(
                    answer="domain.crypto",
                    confidence=0.8,
                    reasoning_trace="Hyperlex instrumental observation",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.LEXICAL_SEMANTIC,
            confidence=0.8,
            uncertainty=0.2,
            provenance={
                "source": "hyperlex",
                "authority": "advisory",
                "semantic_truth": False,
                "influence_policy": "NONE",
                "valid_for_forecast": False,
                "lane": "shadow",
            }
        )
        
        # Run through arbiter
        decision = orchestrator.arbiter.arbitrate(envelope)
        
        # Decision should be a valid Decision enum value
        from abraxas.evidence.contract import Decision
        assert isinstance(decision, Decision)
        assert decision in [Decision.ACCEPT, Decision.VERIFY, Decision.RECOMPUTE, Decision.ABSTAIN, Decision.ESCALATE]
        
        # Check audit log
        audit = orchestrator.arbiter.get_audit_log()
        assert len(audit) >= 1
        assert audit[-1]["event"] == "ARBITRATION_COMPLETE"
        assert audit[-1]["details"]["evidence_id"] == envelope.evidence_id

    def test_evidence_through_six_gate_governor(self):
        """HYPERLEX evidence should pass through 6-gate governor."""
        from abraxas.governance.production import ProductionOrchestrator, EngineStatus
        from abraxas.evidence.policy import DecisionRecord
        from abraxas.evidence.provider import EvidenceProvider
        from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, Decision
        
        orchestrator = ProductionOrchestrator()
        
        # Register mock hyperlex provider
        class HyperlexProvider(EvidenceProvider):
            engine_name = "hyperlex"
            engine_version = "v1"
            supported_evidence_types = [EvidenceType.LEXICAL_SEMANTIC]
            
            def get_model_identity(self):
                return "hyperlex-instrument-v1"
            
            def produce_evidence(self, request_id, claim, context, budget=None):
                return EvidenceEnvelope(
                    engine=self.engine_name,
                    engine_version=self.engine_version,
                    model_identity=self.get_model_identity(),
                    request_id=request_id,
                    claim=claim,
                    candidate_outputs=[
                        CandidateOutput(
                            answer="domain.crypto",
                            confidence=0.85,
                            reasoning_trace="Hyperlex instrumental observation",
                            relation_steps=[]
                        )
                    ],
                    evidence_type=EvidenceType.LEXICAL_SEMANTIC,
                    confidence=0.85,
                    uncertainty=0.15,
                    provenance={
                        "source": "hyperlex",
                        "authority": "advisory",
                        "semantic_truth": False,
                        "influence_policy": "NONE",
                        "valid_for_forecast": False,
                        "lane": "shadow",
                    }
                )
        
        orchestrator.engine_registry.register(HyperlexProvider())
        orchestrator.engine_registry.update_health("hyperlex", EngineStatus.HEALTHY, latency_ms=10.0)
        
        envelope = EvidenceEnvelope(
            engine="hyperlex",
            engine_version="v1",
            model_identity="hyperlex-instrument-v1",
            request_id="test-q1-002",
            claim="Test hyperlex 6-gate",
            candidate_outputs=[
                CandidateOutput(
                    answer="domain.crypto",
                    confidence=0.85,
                    reasoning_trace="Hyperlex instrumental observation",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.LEXICAL_SEMANTIC,
            confidence=0.85,
            uncertainty=0.15,
            provenance={
                "source": "hyperlex",
                "authority": "advisory",
                "semantic_truth": False,
                "influence_policy": "NONE",
                "valid_for_forecast": False,
                "lane": "shadow",
            }
        )
        
        decision = orchestrator.arbiter.arbitrate(envelope)
        
        record = DecisionRecord.from_arbitration(
            request_id="test-q1-002",
            envelopes=[envelope],
            decision=decision,
            confidence=envelope.confidence,
        )
        
        governance = orchestrator.governor.evaluate(record)
        
        assert "governed" in governance
        assert "aggregate_score" in governance
        assert "gate_results" in governance
        assert len(governance["gate_results"]) == 6
        
        # Check all 6 gates present
        gate_names = {g["gate"] for g in governance["gate_results"]}
        expected_gates = {
            "provenance", "falsifiability", "redundancy",
            "rent", "ablation", "stabilization"
        }
        assert gate_names == expected_gates


class TestHYPERLEX_Q1_FeatureFlag:
    """Tests for feature flag behavior."""

    def test_feature_flag_default_off(self, monkeypatch):
        """Feature flag defaults to off."""
        monkeypatch.delenv("ABX_HYPERLEX_INSTRUMENT", raising=False)
        assert instrument_enabled() is False

    def test_feature_flag_can_enable(self, monkeypatch):
        """Feature flag can be enabled."""
        monkeypatch.setenv("ABX_HYPERLEX_INSTRUMENT", "1")
        assert instrument_enabled() is True

    def test_observe_text_disabled_without_flag(self, monkeypatch):
        """observe_text returns disabled without flag."""
        monkeypatch.delenv("ABX_HYPERLEX_INSTRUMENT", raising=False)
        result = observe_text("test")
        assert result["ok"] is False
        assert result["error"] == "ABX_HYPERLEX_INSTRUMENT_disabled"


class TestHYPERLEX_Q1_Schema:
    """Tests for schema validation."""

    def test_subsystem_yaml_exists(self):
        """Subsystem YAML exists with correct configuration."""
        subsystem_path = Path(__file__).parent.parent.parent / ".abraxas" / "subsystems" / "hyperlex_instrument_v1.yaml"
        assert subsystem_path.exists()
        
        import yaml
        with open(subsystem_path) as f:
            config = yaml.safe_load(f)
        
        assert config["subsystem_id"] == "hyperlex_instrument_v1"
        assert config["canon_status"] == "shadow_advisory"
        assert config["lane"] == "shadow"
        assert config["promotion_state"] == "candidate"
        assert "shadow_only_until_explicit_promotion" in config["promotion_requirements"]
        assert "no_forecast_influence" in config["promotion_requirements"]
        assert "hyperlex_output_not_semantic_truth" in config["promotion_requirements"]
        assert "classifier_release_remains_rejected" in config["promotion_requirements"]


# Entry point for manual execution
if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "--tb=short"])