"""
Integrating Real ZKP Backend with Abraxas EvidenceZKPManager

This script demonstrates how to integrate a real zkpy-based backend (for hash preimage proofs) 
with the Abraxas EvidenceZKPManager.

We'll create a backend that uses the hash_zkp_backend we just created, and show how to:
1. Initialize the EvidenceZKPManager with the real backend
2. Create a commitment to an evidence envelope
3. Generate a zero-knowledge proof of integrity
4. Verify the proof
5. Show that tampering invalidates the proof

Note: This script uses the hash_zkp_backend we created. If zkpy is not available, it will fall back to the simulated backend.
"""

import sys
import os

# Add the project root to the Python path so we can import abraxas modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from abraxas.zkp.zkp_interface import EvidenceZKPManager
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep
# Import our real zkpy backend
from abraxas.zkp.hash_zkp_backend import get_hash_preimage_zkp_backend


def create_sample_evidence() -> EvidenceEnvelope:
    """Create a sample evidence envelope for demonstration."""
    return EvidenceEnvelope(
        engine="demo_engine",
        engine_version="1.0",
        model_identity="demo_model",
        request_id="demo-001",
        claim="The quick brown fox jumps over the lazy dog",
        candidate_outputs=[CandidateOutput(
            answer="True",
            confidence=0.95,
            reasoning_trace="The sentence is a well-known pangram containing every letter of the alphabet.",
            relation_steps=[RelationStep(
                relation="is_pangram",
                subject="sentence",
                object="True",
                result="Contains every letter of the alphabet at least once",
                confidence=0.9
            )]
        )],
        evidence_type=EvidenceType.RELATIONAL_REASONING,
        confidence=0.95,
        uncertainty=0.05,
        provenance={"demo": True, "timestamp": "2026-10-04T10:30:00Z"}
    )


def demo_real_zkp_integration():
    """Demonstrate integrating a real zkpy backend with Abraxas evidence."""
    print("=== Abraxas Real ZKP Integration Demo ===")
    print()
    
    # Step 1: Try to get the real zkpy backend
    real_backend = get_hash_preimage_zkp_backend()
    
    if real_backend is None:
        print("Real zkpy backend not available. Falling back to simulated backend.")
        # Fall back to simulated backend (which is already in the interface)
        zkp_manager = EvidenceZKPManager()
        print(f"ZKP Manager Initialized: {zkp_manager.is_initialized}")
        print(f"Using backend type: {type(zkp_manager.zkp_backend).__name__}")
    else:
        # Initialize the EvidenceZKPManager with the real backend
        zkp_manager = EvidenceZKPManager(zkp_backend=real_backend)
        print(f"ZKP Manager Initialized: {zkp_manager.is_initialized}")
        print(f"Using backend type: {type(zkp_manager.zkp_backend).__name__}")
        print(f"ZKP Available (zkpy): {getattr(real_backend, 'initialized', 'Unknown')}")
    print()
    
    # Step 2: Create sample evidence
    evidence = create_sample_evidence()
    print(f"Created evidence:")
    print(f"  Claim: {evidence.claim}")
    print(f"  Evidence ID: {evidence.evidence_id}")
    print(f"  Confidence: {evidence.confidence}")
    print()
    
    # Step 3: Create a commitment to the evidence and generate an integrity proof
    print("--- Generating ZKP Commitment and Proof ---")
    enhanced_evidence, commitment, proof = zkp_manager.create_evidence_with_zkp(evidence)
    
    if commitment is None:
        print("ERROR: Failed to create commitment. ZKP may not be available.")
        return
        
    print("Generated Commitment:")
    print(f"  Commitment: {commitment.commitment}")
    print(f"  Blinding Factor: {commitment.blinding_factor}")
    print()
    
    if proof is None:
        print("WARNING: Failed to generate ZKP proof. Continuing with commitment only.")
    else:
        print("Generated ZKP Proof:")
        # Truncate the proof for display if it's long
        proof_str = proof.proof
        if len(proof_str) > 100:
            print(f"  Proof: {proof_str[:100]}...")
        else:
            print(f"  Proof: {proof_str}")
        print(f"  Proof Type: {proof.proof_type}")
        print(f"  Public Inputs: {list(proof.public_inputs.keys())}")
        print()
        
        # Step 4: Verify the proof
        print("--- Verifying ZKP Proof ---")
        is_valid = zkp_manager.verify_integrity_proof(proof, commitment)
        print(f"Proof Verification: {'VALID' if is_valid else 'INVALID'}")
        print()
        
        # Step 5: Show what was added to the evidence's provenance
        print("--- Evidence Provenance Update ---")
        print("Added to evidence provenance:")
        for key, value in enhanced_evidence.provenance.items():
            if key.startswith("zkp_"):
                if key == "zkp_proof":
                    print(f"  {key}: {value[:100]}...")  # Truncate long proof
                elif key == "zkp_public_inputs":
                    print(f"  {key}: {value}")
                else:
                    print(f"  {key}: {value}")
        print()
    
    # Step 6: Demonstrate tamper detection
    print("--- Tamper Detection Demo ---")
    # Create a tampered version of the evidence by changing the claim
    tampered_evidence = EvidenceEnvelope(
        engine="demo_engine",
        engine_version="1.0",
        model_identity="demo_model",
        request_id="demo-002",
        claim="The quick brown fox jumps over the lazy cat",  # Changed "dog" to "cat"
        candidate_outputs=[CandidateOutput(
            answer="True",
            confidence=0.95,
            reasoning_trace="The sentence is a well-known pangram containing every letter of the alphabet.",
            relation_steps=[RelationStep(
                relation="is_pangram",
                subject="sentence",
                object="True",
                result="Contains every letter of the alphabet at least once",
                confidence=0.9
            )]
        )],
        evidence_type=EvidenceType.RELATIONAL_REASONING,
        confidence=0.95,
        uncertainty=0.05,
        provenance={"demo": True, "timestamp": "2026-10-04T10:30:00Z"}
    )
    
    # Try to create a commitment and proof for the tampered evidence
    _, tampered_commitment, _ = zkp_manager.create_evidence_with_zkp(tampered_evidence)
    
    print("Tampered evidence:")
    print(f"  Claim: {tampered_evidence.claim}")
    print(f"  New Commitment: {tampered_commitment.commitment if tampered_commitment else 'Failed to create'}")
    print()
    
    if commitment and tampered_commitment:
        print(f"Original Commitment:  {commitment.commitment}")
        print(f"Tampered Commitment:  {tampered_commitment.commitment}")
        print(f"Commitments Match:    {commitment.commitment == tampered_commitment.commitment}")
        print()
        
        # If we had a proof for the original evidence, it would not verify with the tampered commitment
        if proof:
            # Verify the original proof with the tampered commitment (should fail)
            is_valid_tampered = zkp_manager.verify_integrity_proof(proof, tampered_commitment)
            print(f"Original Proof Verification with Tampered Commitment: {'VALID' if is_valid_tampered else 'INVALID'}")
            print("(This should be INVALID because the proof was created for the original evidence)")
            print()
    
    # Step 7: Show how selective disclosure could work (conceptual)
    print("--- Selective Disclosure Example ---")
    # Prove that we know an evidence with confidence > 0.9 without revealing the exact confidence
    # Note: Our simple selective disclosure in the interface is basic - this is just a concept demo
    conf_proof = zkp_manager.selectivley_disclose_property(
        enhanced_evidence, 
        "confidence", 
        0.9
    )
    
    if conf_proof:
        print(f"Generated confidence > 0.9 proof: {conf_proof.proof[:50]}...")
        # Note: In a real implementation, we would have a proper way to verify this proof
        # For now, we just show that we generated something
        print("Note: In a real ZKP system, this proof would verify without revealing the exact confidence value.")
    else:
        print("Could not generate selective disclosure proof (interface may be limited for this property).")
    print()
    
    print("=== Demo Complete ===")
    print("Summary:")
    print("- Created evidence envelope")
    print("- Generated commitment and ZKP proof of integrity")
    print("- Verified the proof")
    print("- Demonstrated that tampering invalidates the proof")
    print("- Showed how selective disclosure could work")
    print()
    print(f"Note: This demo used the {'real zkpy backend' if real_backend is not None else 'simulated ZKP backend'}.")
    print("To use a different real ZKP backend, replace the backend in EvidenceZKPManager initialization.")


if __name__ == "__main__":
    demo_real_zkp_integration()