"""
Demonstration of ZKP for Evidence Integrity in Abraxas.

This script shows how to use the ZKP interface to:
1. Create a commitment to an evidence envelope
2. Generate a zero-knowledge proof of integrity (proving knowledge of the preimage of the commitment)
3. Verify the proof
4. Show that tampering with the evidence invalidates the proof

Note: This demonstration uses the simulated ZKP backend for simplicity.
To use a real ZKP backend (e.g., based on zkpy), simply replace the backend in the EvidenceZKPManager initialization.
"""

import sys
import os
# Add the project root to the Python path so we can import abraxas modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from abraxas.zkp.zkp_interface import EvidenceZKPManager, ZKPCommitment, ZKPProof
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep


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


def demo_evidence_integrity_zkp():
    """Demonstrate ZKP for evidence integrity."""
    print("=== Abraxas Evidence Integrity ZKP Demo ===")
    print()
    
    # Step 1: Initialize the ZKP manager with the simulated backend
    # In production, you would replace SimulatedZKPBackend with a real backend (e.g., hash_preimage_zkp_backend)
    zkp_manager = EvidenceZKPManager()
    print(f"ZKP Manager Initialized: {zkp_manager.is_initialized}")
    print(f"Using backend type: {type(zkp_manager.zkp_backend).__name__}")
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
        print(f"  Proof: {proof.proof[:100]}...")  # Truncate for display
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
    tampered_evidence = evidence  # Start with the original
    tampered_evidence.claim = "The quick brown fox jumps over the lazy cat"  # Changed "dog" to "cat"
    
    # Try to create a commitment and proof for the tampered evidence
    # Note: In a real system, we would not have the original blinding factor for the tampered evidence
    # For this demo, we'll show that if we tried to verify the original proof with the tampered evidence, it would fail
    
    # Create a new commitment for the tampered evidence (with a new random blinding factor)
    tampered_commitment = zkp_manager.create_evidence_commitment(tampered_evidence)
    
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
    
    # Step 7: Show how selective disclosure could work
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
    print("Note: This demo used the simulated ZKP backend.")
    print("To use a real ZKP backend (e.g., based on zkpy for hash preimage or square root proofs),")
    print("replace the backend in EvidenceZKPManager initialization.")


if __name__ == "__main__":
    demo_evidence_integrity_zkp()