"""SEMION-Q1 Qualification Test Suite

This test suite validates the SEMION-Q1 qualification gates using the
deterministic fixtures defined in semion_q1_fixtures.yaml.

Run with: python -m pytest abraxas/evidence/test_semion_q1.py -v
"""

from __future__ import annotations

import os
import yaml
import pytest
from pathlib import Path

from abraxas.evidence.contract import (
    EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep, Decision
)
from abraxas.evidence.verifiers.sign import (
    parse_sign_class, validate_sign_class, check_interpretant_coherence,
    check_representamen_object_alignment, PEIRCE_CLASSES, VALID_COMBINATIONS
)


FIXTURES_PATH = Path(__file__).parent / "semion_q1_fixtures.yaml"


def load_fixtures() -> dict:
    """Load test fixtures from YAML."""
    with open(FIXTURES_PATH) as f:
        return yaml.safe_load(f)


class TestSEMION_Q1_Specification:
    """Tests for SEMION-Q1 specification compliance."""

    def test_spec_file_exists(self):
        """Verify the specification document exists."""
        spec_path = Path(__file__).parent / "semion_sign_relation_v1.spec.md"
        assert spec_path.exists(), "SEMION-Q1 specification document missing"

    def test_spec_contains_required_sections(self):
        """Verify specification has all required gates documented."""
        spec_path = Path(__file__).parent / "semion_sign_relation_v1.spec.md"
        content = spec_path.read_text()
        
        required_sections = [
            "Qualification Gates",
            "Wire-Shape Contract",
            "Peircean Sign Classification",
            "Invariants",
            "Test Fixtures",
            "Qualification Receipt Structure",
            "Pairwise Conformance",
        ]
        
        for section in required_sections:
            assert section in content, f"Missing required section: {section}"


class TestSEMION_Q1_PeirceanValidation:
    """Tests for Peircean sign class validation (core SEMION logic)."""

    @pytest.fixture(scope="class")
    @classmethod
    def fixtures(self):
        return load_fixtures()

    def test_all_27_combinations_valid(self):
        """All 27 Peircean combinations should be valid."""
        assert len(VALID_COMBINATIONS) == 27
        
        # Verify each combination structure
        for combo in VALID_COMBINATIONS:
            assert len(combo) == 3
            existence, thirdness, relation = combo
            assert existence in ["qualisign", "sinsign", "legisign"]
            assert thirdness in ["rheme", "dicent", "argument"]
            assert relation in ["icon", "index", "symbol"]

    def test_parse_sign_class_valid(self):
        """parse_sign_class should correctly parse valid sign classes."""
        test_cases = [
            ("qualisign-rheme-icon", ("qualisign", "rheme", "icon")),
            ("sinsign-dicent-index", ("sinsign", "dicent", "index")),
            ("legisign-argument-symbol", ("legisign", "argument", "symbol")),
        ]
        
        for sign_class, expected in test_cases:
            result = parse_sign_class(sign_class)
            assert result == expected, f"Failed for {sign_class}"

    def test_parse_sign_class_invalid_format(self):
        """parse_sign_class should return None for invalid format."""
        invalid_cases = [
            "invalid",
            "qualisign-rheme",
            "qualisign-rheme-icon-extra",
            "",
        ]
        
        for sign_class in invalid_cases:
            result = parse_sign_class(sign_class)
            assert result is None, f"Should return None for {sign_class}"

    def test_validate_sign_class_all_valid(self, fixtures):
        """All 27 valid combinations should pass validation."""
        fixture = fixtures["fixture_all_27_valid_combinations"]
        
        for sign_class in fixture["combinations"]:
            valid, errors = validate_sign_class(sign_class)
            assert valid is True, f"Should be valid: {sign_class}, errors: {errors}"
            assert errors == [], f"Should have no errors: {errors}"

    def test_validate_sign_class_invalid_format(self):
        """Invalid format should fail validation."""
        valid, errors = validate_sign_class("invalid-format")
        assert valid is False
        assert len(errors) == 1
        assert "Invalid sign class format" in errors[0]

    def test_validate_sign_class_invalid_existence(self):
        """Invalid existence should fail validation."""
        valid, errors = validate_sign_class("invalid-rheme-icon")
        assert valid is False
        assert any("Invalid existence" in e for e in errors)

    def test_validate_sign_class_invalid_thirdness(self):
        """Invalid thirdness should fail validation."""
        valid, errors = validate_sign_class("qualisign-invalid-icon")
        assert valid is False
        assert any("Invalid thirdness" in e for e in errors)

    def test_validate_sign_class_invalid_relation(self):
        """Invalid relation should fail validation."""
        valid, errors = validate_sign_class("qualisign-rheme-invalid")
        assert valid is False
        assert any("Invalid relation" in e for e in errors)


class TestSEMION_Q1_InterpretantCoherence:
    """Tests for interpretant coherence checking."""

    def test_valid_causal_chain(self):
        """Valid causal relations should have high coherence."""
        steps = [
            {"relation": "causes", "subject": "a", "object": "b", "result": "b happens"},
            {"relation": "implies", "subject": "b happens", "object": "c", "result": "c follows"},
        ]
        
        coherence, errors = check_interpretant_coherence(steps)
        assert coherence == 1.0
        assert errors == []

    def test_contradictory_causal(self):
        """Causal relation with negated result should have 0 coherence."""
        steps = [
            {"relation": "causes", "subject": "a", "object": "b", "result": "not b"},
        ]
        
        coherence, errors = check_interpretant_coherence(steps)
        assert coherence == 0.0
        assert len(errors) == 1
        assert "Contradictory" in errors[0]

    def test_contradictory_implies(self):
        """Implies with negated result should have 0 coherence."""
        steps = [
            {"relation": "implies", "subject": "a", "object": "b", "result": "not b"},
        ]
        
        coherence, errors = check_interpretant_coherence(steps)
        assert coherence == 0.0
        assert "Contradictory" in errors[0]

    def test_empty_steps(self):
        """Empty steps should return 1.0 coherence."""
        coherence, errors = check_interpretant_coherence([])
        assert coherence == 1.0
        assert errors == []


class TestSEMION_Q1_RepresentamenObjectAlignment:
    """Tests for representamen-object alignment (chain continuity)."""

    def test_perfect_chain(self):
        """Perfect chain (object == next subject) should have 1.0 alignment."""
        steps = [
            {"relation": "means", "subject": "word1", "object": "concept1"},
            {"relation": "implies", "subject": "concept1", "object": "concept2"},
            {"relation": "causes", "subject": "concept2", "object": "effect"},
        ]
        
        alignment = check_representamen_object_alignment(steps)
        assert alignment == 1.0

    def test_broken_chain(self):
        """Broken chain should have 0.0 alignment."""
        steps = [
            {"relation": "means", "subject": "word1", "object": "concept1"},
            {"relation": "implies", "subject": "unrelated", "object": "concept2"},
        ]
        
        alignment = check_representamen_object_alignment(steps)
        assert alignment == 0.0

    def test_partial_chain(self):
        """Partial chain alignment."""
        steps = [
            {"relation": "means", "subject": "word1", "object": "concept1"},
            {"relation": "implies", "subject": "concept1", "object": "concept2"},
            {"relation": "causes", "subject": "wrong", "object": "effect"},
        ]
        
        alignment = check_representamen_object_alignment(steps)
        assert alignment == 0.5  # 1 out of 2 transitions match

    def test_single_step(self):
        """Single step should return 1.0."""
        alignment = check_representamen_object_alignment([{"subject": "a", "object": "b"}])
        assert alignment == 1.0


class TestSEMION_Q1_Fixtures:
    """Tests using the deterministic Q1 fixtures."""

    @pytest.fixture(scope="class")
    @classmethod
    def fixtures(self):
        return load_fixtures()

    def test_fixture_valid_qualisign_rheme_icon(self, fixtures):
        """Test valid qualisign-rheme-icon fixture."""
        fixture = fixtures["fixture_valid_qualisign_rheme_icon"]
        input_obs = fixture["input"]
        
        # Validate sign class
        valid, errors = validate_sign_class(input_obs["sign_class"])
        assert valid is True
        assert errors == []
        
        # Check interpretant coherence
        coherence, errors = check_interpretant_coherence(input_obs["relation_steps"])
        assert coherence == input_obs["interpretant_coherence"]
        
        # Check representamen-object alignment
        alignment = check_representamen_object_alignment(input_obs["relation_steps"])
        assert alignment == input_obs["representamen_object_alignment"]
        
        # Check Peircean analysis
        assert input_obs["peircean_analysis"]["valid_combination"] is True

    def test_fixture_valid_sinsign_dicent_index(self, fixtures):
        """Test valid sinsign-dicent-index fixture."""
        fixture = fixtures["fixture_valid_sinsign_dicent_index"]
        input_obs = fixture["input"]
        
        valid, errors = validate_sign_class(input_obs["sign_class"])
        assert valid is True
        
        coherence, _ = check_interpretant_coherence(input_obs["relation_steps"])
        assert coherence == 1.0  # No contradictions in this fixture
        
        alignment = check_representamen_object_alignment(input_obs["relation_steps"])
        # smoke -> fire -> heat is a perfect chain
        assert alignment == 1.0

    def test_fixture_valid_legisign_argument_symbol(self, fixtures):
        """Test valid legisign-argument-symbol fixture."""
        fixture = fixtures["fixture_valid_legisign_argument_symbol"]
        input_obs = fixture["input"]
        
        valid, errors = validate_sign_class(input_obs["sign_class"])
        assert valid is True

    def test_fixture_invalid_format(self, fixtures):
        """Test invalid format fixture."""
        fixture = fixtures["fixture_invalid_format"]
        # Build full input from base fixture + modification
        base = fixtures["fixture_valid_qualisign_rheme_icon"]["input"]
        input_obs = base.copy()
        input_obs.update(fixture["input_modification"])
        
        valid, errors = validate_sign_class(input_obs["sign_class"])
        assert valid is False
        assert fixture["input_modification"]["sign_class_errors"] == errors

    def test_fixture_invalid_existence(self, fixtures):
        """Test invalid existence fixture."""
        fixture = fixtures["fixture_invalid_existence"]
        base = fixtures["fixture_valid_qualisign_rheme_icon"]["input"]
        input_obs = base.copy()
        input_obs.update(fixture["input_modification"])
        
        valid, errors = validate_sign_class(input_obs["sign_class"])
        assert valid is False
        assert fixture["input_modification"]["sign_class_errors"] == errors

    def test_fixture_invalid_thirdness(self, fixtures):
        """Test invalid thirdness fixture."""
        fixture = fixtures["fixture_invalid_thirdness"]
        base = fixtures["fixture_valid_qualisign_rheme_icon"]["input"]
        input_obs = base.copy()
        input_obs.update(fixture["input_modification"])
        
        valid, errors = validate_sign_class(input_obs["sign_class"])
        assert valid is False
        assert fixture["input_modification"]["sign_class_errors"] == errors

    def test_fixture_invalid_relation(self, fixtures):
        """Test invalid relation fixture."""
        fixture = fixtures["fixture_invalid_relation"]
        base = fixtures["fixture_valid_qualisign_rheme_icon"]["input"]
        input_obs = base.copy()
        input_obs.update(fixture["input_modification"])
        
        valid, errors = validate_sign_class(input_obs["sign_class"])
        assert valid is False
        assert fixture["input_modification"]["sign_class_errors"] == errors

    def test_fixture_contradictory_interpretant(self, fixtures):
        """Test contradictory interpretant fixture."""
        fixture = fixtures["fixture_contradictory_interpretant"]
        input_obs = fixture["input"]
        
        # Sign class is valid
        valid, errors = validate_sign_class(input_obs["sign_class"])
        assert valid is True
        
        # But interpretant coherence should be 0
        coherence, errors = check_interpretant_coherence(input_obs["relation_steps"])
        assert coherence == fixture["expected_interpretant_coherence"]

    def test_fixture_broken_chain(self, fixtures):
        """Test broken chain fixture."""
        fixture = fixtures["fixture_broken_chain"]
        input_obs = fixture["input"]
        
        # Sign class is valid
        valid, errors = validate_sign_class(input_obs["sign_class"])
        assert valid is True
        
        # But alignment should be 0
        alignment = check_representamen_object_alignment(input_obs["relation_steps"])
        assert alignment == fixture["expected_alignment"]


class TestSEMION_Q1_AuthorityBoundary:
    """Tests for authority boundary enforcement (via existing verifier logic)."""

    def test_peirce_classes_structure(self):
        """PEIRCE_CLASSES should have all 9 categories."""
        assert len(PEIRCE_CLASSES) == 9
        
        categories = set()
        for cls, info in PEIRCE_CLASSES.items():
            assert "category" in info
            assert "type" in info
            categories.add(info["category"])
        
        assert categories == {"firstness", "secondness", "thirdness"}

    def test_valid_combinations_count(self):
        """VALID_COMBINATIONS should have exactly 27 entries."""
        assert len(VALID_COMBINATIONS) == 27
        
        # All combinations of 3×3×3 = 27
        existences = ["qualisign", "sinsign", "legisign"]
        thirdnesses = ["rheme", "dicent", "argument"]
        relations = ["icon", "index", "symbol"]
        
        expected = set()
        for e in existences:
            for t in thirdnesses:
                for r in relations:
                    expected.add((e, t, r))
        
        assert VALID_COMBINATIONS == expected


def _instrument_envelope(fixture_name: str, request_id: str, claim: str):
    """Build an EvidenceEnvelope from one of the repo's OWN SEMION fixtures.

    The integration tests used to type their envelopes in by hand — the same
    `answer="qualisign-rheme-icon"`, `confidence=0.85` literal appearing twice in one method. That proved
    arbitration accepts a dict SHAPED like semion evidence, using a number this file invented. Driving the
    real fixture through abraxas.evidence.semion_instrument instead means the integration tests now exercise
    semion's actual boundary: the confidence is the frame's own coherence, and every authority field comes
    from the frame rather than from the test author.
    """
    from abraxas.evidence.semion_instrument import adapt_observation, to_evidence_envelope

    frame = load_fixtures()[fixture_name]["input"]
    envelope = to_evidence_envelope(
        adapt_observation(frame), request_id=request_id, claim=claim
    )
    return envelope, frame


class TestSEMION_Q1_Integration:
    """Integration tests with ProductionArbiter."""

    def test_semion_evidence_through_production_arbiter(self):
        """SEMION evidence should arbitrate through ProductionArbiter."""
        from abraxas.governance.production import ProductionOrchestrator, EngineStatus
        from abraxas.evidence.provider import EvidenceProvider

        envelope, frame = _instrument_envelope(
            "fixture_valid_qualisign_rheme_icon", "test-q1-001", "Test semion integration"
        )

        # The confidence is the fixture's own coherence, not a literal chosen here.
        assert envelope.confidence == pytest.approx(
            frame["peircean_analysis"]["coherence_score"]
        )
        assert envelope.provenance["lane"] == "shadow"
        assert envelope.provenance["influence_policy"] == "NONE"
        assert envelope.provenance["valid_for_forecast"] is False

        orchestrator = ProductionOrchestrator()

        # Registered so the arbiter has an engine to attribute the evidence to. The envelope it returns is
        # the instrument's; this class exists for registration only.
        class SemionProvider(EvidenceProvider):
            engine_name = "semion"
            engine_version = "semion.sign.v1"
            supported_evidence_types = [EvidenceType.SIGN_RELATION]

            def get_model_identity(self):
                return "semion-sign-v1"

            def produce_evidence(self, request_id, claim, context, budget=None):
                return envelope

        orchestrator.engine_registry.register(SemionProvider())
        orchestrator.engine_registry.update_health("semion", EngineStatus.HEALTHY, latency_ms=10.0)

        # Run through arbiter
        decision = orchestrator.arbiter.arbitrate(envelope)

        assert isinstance(decision, Decision)
        assert decision in [Decision.ACCEPT, Decision.VERIFY, Decision.RECOMPUTE, Decision.ABSTAIN, Decision.ESCALATE]

        # Check audit log
        audit = orchestrator.arbiter.get_audit_log()
        assert len(audit) >= 1
        assert audit[-1]["event"] == "ARBITRATION_COMPLETE"

    def test_semion_evidence_through_six_gate_governor(self):
        """SEMION evidence should pass through 6-gate governor."""
        from abraxas.governance.production import ProductionOrchestrator, EngineStatus
        from abraxas.evidence.policy import DecisionRecord
        from abraxas.evidence.provider import EvidenceProvider

        envelope, frame = _instrument_envelope(
            "fixture_valid_sinsign_dicent_index", "test-q1-002", "Test semion 6-gate"
        )

        # The fixture's own coherence for this frame is 0.88. The hand-typed envelope this replaces asserted
        # 0.9 — so that literal was not merely redundant, it disagreed with the fixture it stood in for.
        assert envelope.confidence == pytest.approx(
            frame["peircean_analysis"]["coherence_score"]
        )
        assert envelope.confidence != 0.9, "0.9 was the hand-typed value, not the fixture's"

        orchestrator = ProductionOrchestrator()

        class SemionProvider(EvidenceProvider):
            engine_name = "semion"
            engine_version = "semion.sign.v1"
            supported_evidence_types = [EvidenceType.SIGN_RELATION]

            def get_model_identity(self):
                return "semion-sign-v1"

            def produce_evidence(self, request_id, claim, context, budget=None):
                return envelope

        orchestrator.engine_registry.register(SemionProvider())
        orchestrator.engine_registry.update_health("semion", EngineStatus.HEALTHY, latency_ms=10.0)

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

        gate_names = {g["gate"] for g in governance["gate_results"]}
        expected_gates = {
            "provenance", "falsifiability", "redundancy",
            "rent", "ablation", "stabilization"
        }
        assert gate_names == expected_gates


class TestSEMION_Q1_Verifier:
    """Tests for SignRelationVerifier integration."""

    def test_sign_relation_verifier_exists(self):
        """SignRelationVerifier should be registered for SIGN_RELATION type."""
        from abraxas.evidence.verifiers.sign import SignRelationVerifier
        from abraxas.governance.production import ProductionOrchestrator
        
        orchestrator = ProductionOrchestrator()
        # Check that verifier is registered in arbiter
        verifier = orchestrator.arbiter.arbiter._verifiers.get("SIGN_RELATION")
        assert verifier is not None
        assert isinstance(verifier, SignRelationVerifier)

    def test_sign_verifier_verify_method(self):
        """SignRelationVerifier.verify should return expected structure."""
        from abraxas.evidence.verifiers.sign import SignRelationVerifier

        verifier = SignRelationVerifier()

        # Built from a SEMION fixture through the instrument, like the integration tests: the verifier is
        # exercised on evidence of the shape it will actually receive, rather than on a hand-assembled
        # envelope whose candidate answer this file chose.
        envelope, _frame = _instrument_envelope(
            "fixture_valid_qualisign_rheme_icon", "test-verify-001", "Test sign verification"
        )

        result = verifier.verify(envelope)

        assert "passed" in result
        assert "escalate" in result
        assert "details" in result
        # Check actual keys from implementation
        assert "sign_class_valid" in result["details"]
        assert "interpretant_coherence" in result["details"]
        assert "representamen_object_alignment" in result["details"]
        assert "peircean_category_consistency" in result["details"]
        assert "thirdness_recursion" in result["details"]
        assert "total_steps" in result["details"]
        assert "contradictions" in result["details"]


# Entry point for manual execution
if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "--tb=short"])