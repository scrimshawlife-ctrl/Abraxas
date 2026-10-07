#!/usr/bin/env python3
"""
Test script for Oracle adapter with context-aware narrative synthesis
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from abraxas.evidence.adapters.oracle import create_oracle_adapter
from abraxas.evidence.contract import EvidenceEnvelope

def test_oracle_adapter():
    """Test the Oracle adapter with context-aware narrative synthesis"""
    print("Testing Oracle adapter with context-aware narrative synthesis...")
    
    # Create adapter
    adapter = create_oracle_adapter()
    
    # Test claim
    claim = "Why does the moon orbit the Earth?"
    context = {
        "domain": "astronomy",
        "complexity": "intermediate",
        "user_expertise": "beginner"
    }
    
    # Produce evidence
    envelope = adapter.produce_evidence(
        request_id="test-oracle-001",
        claim=claim,
        context=context
    )
    
    # Verify envelope properties
    assert envelope.engine == "oracle"
    assert envelope.engine_version == "0.1.0"
    assert envelope.claim == claim
    assert envelope.evidence_type.value == "NARRATIVE_SYNTHESIS"
    assert len(envelope.candidate_outputs) >= 1
    assert 0.0 <= envelope.confidence <= 1.0
    assert 0.0 <= envelope.uncertainty <= 1.0
    assert abs(envelope.confidence + envelope.uncertainty - 1.0) < 0.001
    
    # Check provenance: it names the path that ran, and the input it ran on.
    #
    # This replaced assertions on `engine`, `enhancement_version` and `analysis_timestamp` -- keys the deleted
    # keyword heuristic wrote about itself. The provenance of an inference-backed reading should say which
    # inference path produced it and what it was given, not what the adapter calls itself.
    assert "source" in envelope.provenance
    assert "inference" in envelope.provenance
    assert envelope.provenance["inference"] in {"offline-deterministic", "http"}, envelope.provenance
    assert "input_sha256" in envelope.provenance
    
    # Check reasoning steps
    assert len(envelope.reasoning_steps) >= 1
    
    # Check relations
    assert len(envelope.relations) >= 1
    
    print(f"✅ Oracle adapter test passed!")
    print(f"   Engine: {envelope.engine}")
    print(f"   Evidence Type: {envelope.evidence_type.value}")
    print(f"   Confidence: {envelope.confidence:.3f}")
    print(f"   Candidates: {len(envelope.candidate_outputs)}")
    print(f"   Reasoning Steps: {len(envelope.reasoning_steps)}")
    print(f"   Relations: {envelope.relations}")
    
    # Print candidate details
    for i, candidate in enumerate(envelope.candidate_outputs):
        print(f"   Candidate {i+1}:")
        print(f"     Answer: {candidate.answer}")
        print(f"     Confidence: {candidate.confidence:.3f}")
        print(f"     Reasoning: {candidate.reasoning_trace}")
    
    return True

def test_default_inference_is_model_agnostic():
    """The default path must be the model-agnostic adapter, and must say so honestly.

    This replaces a test that called `_default_oracle_inference` directly. That function is gone: it built a
    `coherence_score` out of word counts and published it as the envelope's confidence, so this test used to
    assert that a keyword heuristic scored 0.0-1.0 -- true, and about nothing. What matters now is the
    opposite property: with no endpoint configured, oracle reports WHICH path ran, and claims no model.
    """
    print("\nTesting that the default inference path is model-agnostic...")

    from abraxas.evidence.adapters.model_agnostic import OFFLINE_IDENTITY, is_configured

    assert not is_configured(), "a model endpoint is configured; this test covers the offline path"

    adapter = create_oracle_adapter()
    test_cases = [
        ("Why is the sky blue?", {"domain": "science"}),
        ("What is the capital of France?", {"domain": "geography"}),
        ("Should we invest in renewable energy?", {"domain": "policy"}),
    ]

    for claim, context in test_cases:
        envelope = adapter.produce_evidence(
            request_id="test-oracle-offline", claim=claim, context=context
        )

        # A reading is produced, and nothing scored it.
        assert len(envelope.candidate_outputs) >= 1
        assert envelope.confidence == 0.0, (
            "the offline path must not invent a confidence; nothing measured this claim"
        )

        # The provenance names the path that ran, and the identity names no model.
        assert envelope.provenance.get("inference") == "offline-deterministic", envelope.provenance
        assert adapter.get_model_identity() == OFFLINE_IDENTITY, adapter.get_model_identity()

        print(f"   Claim: '{claim}' -> {envelope.candidate_outputs[0].answer[:60]}")

    print("✅ Default inference path is model-agnostic and honest about it.")
    return True


def test_an_injected_model_keeps_its_own_identity():
    """When a real model IS injected, its identity and confidences survive -- the adapter must not overwrite
    them. A custom model callable carries `model_identity`; a bare one is reported as unlabelled."""
    from abraxas.evidence.adapters.model_agnostic import identity_of

    def labelled(claim, context):
        return {"candidates": [], "model_identity": "custom/my-model", "relations": [],
                "reasoning_steps": [], "provenance": {}}

    setattr(labelled, "model_identity", "custom/my-model")  # the adapter's own convention

    def unlabelled(claim, context):
        return {"candidates": [], "model_identity": "ignored", "relations": [],
                "reasoning_steps": [], "provenance": {}}

    assert identity_of(labelled) == "custom/my-model"
    assert identity_of(unlabelled) == "custom/unlabelled", (
        "a callable with no declared identity must not be given one"
    )
    print("✅ Injected models keep their own identity; unlabelled ones say so.")
    return True

if __name__ == "__main__":
    try:
        test_default_inference_is_model_agnostic()
        test_an_injected_model_keeps_its_own_identity()
        test_oracle_adapter()
        print("\n🎉 All Oracle adapter tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)