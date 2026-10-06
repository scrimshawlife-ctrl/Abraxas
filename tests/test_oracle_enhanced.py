#!/usr/bin/env python3
"""
Test script for Oracle adapter with context-aware narrative synthesis
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from abraxas.evidence.adapters.oracle import create_oracle_adapter, _default_oracle_inference
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
    
    # Check provenance
    assert "source" in envelope.provenance
    assert "engine" in envelope.provenance
    assert "enhancement_version" in envelope.provenance
    assert "analysis_timestamp" in envelope.provenance
    
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

def test_direct_inference():
    """Test the _default_oracle_inference function directly"""
    print("\nTesting _default_oracle_inference directly...")
    
    # Test different claim types
    test_cases = [
        ("Why is the sky blue?", {"domain": "science"}),
        ("What is the capital of France?", {"domain": "geography"}),
        ("Should we invest in renewable energy?", {"domain": "policy"}),
        ("How does photosynthesis work?", {"domain": "biology"}),
        ("When was the Declaration of Independence signed?", {"domain": "history"})
    ]
    
    for claim, context in test_cases:
        result = _default_oracle_inference(claim, context)
        
        assert "candidates" in result
        assert "model_identity" in result
        assert "relations" in result
        assert "reasoning_steps" in result
        assert "provenance" in result
        
        assert len(result["candidates"]) >= 1
        assert 0.0 <= result["candidates"][0].confidence <= 1.0
        
        print(f"   Claim: '{claim}' -> Tone: {result['candidates'][0].reasoning_trace.split()[3]}")
    
    print("✅ Direct inference test passed!")
    return True

if __name__ == "__main__":
    try:
        test_direct_inference()
        test_oracle_adapter()
        print("\n🎉 All Oracle adapter tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)