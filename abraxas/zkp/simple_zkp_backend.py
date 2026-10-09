"""
Simple zkpy backend for demonstrating ZKP integration with Abraxas.

This backend uses zkpy to prove knowledge of a solution to x^2 = y (mod p)
for a small prime p, to demonstrate the flow without needing complex circuits.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    from zkpy import Circuit, Proof, ProvingKey, VerifierKey  # noqa: F401
    ZKPY_AVAILABLE = True
except ImportError:
    ZKPY_AVAILABLE = False

from abraxas.zkp.zkp_interface import ZKPBackend, ZKPCommitment, ZKPProof


@dataclass
class SquareRootCircuit:
    """
    A simple circuit for proving knowledge of a square root modulo p.
    
    Statement: I know x such that x^2 ≡ y (mod p)
    Witness: x
    Public input: y, p
    """
    
    def __init__(self, prime: int = 101):
        if not ZKPY_AVAILABLE:
            raise ImportError("zkpy is not available. Install with: pip install zkpy")
        
        self.prime = prime
        
        # Define the circuit using zkpy's Python-like DSL
        # We'll create a simple circuit that checks: x * x % p == y
        # Note: Actual zkpy circuits use finite field operations, but for small p we can simulate
        
        self.circuit = Circuit("""
        // Square root circuit: prove knowledge of x such that x^2 = y
        // All operations in the circuit are in the field of integers (we'll simulate mod p)
        
        // Input: witness (x)
        // Public input: y
        // Output: none (we constrain that x*x = y)
        
        // In a real implementation, we would use the field operations properly
        // For this demo with small prime, we can use regular integer operations
        // and rely on the fact that if x*x == y over integers and y < p, then it holds mod p
        // But to be safe, we'll restrict to values where this holds
        
        // Actually, let's use a simpler approach: we'll just check equality
        // and rely on the user to keep values small
        """)
        
        # In a real implementation, we would compile the circuit
        # For this demo, we'll simulate the keys
        self.proving_key = "simulated_proving_key"
        self.verifier_key = "simulated_verifier_key"
    
    def generate_proof(self, witness: int, public_input: int) -> Optional[Dict]:
        """Generate a proof for the square root statement."""
        if not ZKPY_AVAILABLE:
            return None
            
        try:
            # Check that the witness satisfies the statement
            if (witness * witness) % self.prime != public_input % self.prime:
                return None
            
            # In a real implementation, we would:
            # 1. Convert witness and public input to the field
            # 2. Use the proving key to generate a proof
            # 3. Return the proof
            
            # For this demo, we'll create a structured proof that includes
            # the witness (which is NOT zero-knowledge, but shows the flow)
            # In a real ZKP, the witness would not be in the proof
            proof_data = {
                "witness": witness,
                "statement": f"x^2 ≡ {public_input} (mod {self.prime})",
                "proof_data": secrets.token_hex(16)  # Simulated proof data
            }
            
            return {
                "proof": proof_data,
                "public_inputs": [public_input % self.prime, self.prime]
            }
        except Exception as e:
            print(f"Error generating proof: {e}")
            return None
    
    def verify_proof(self, proof: Dict, public_input: int) -> bool:
        """Verify a proof for the square root statement."""
        if not ZKPY_AVAILABLE or not proof:
            return False
            
        try:
            # Extract public input from proof
            proof_public_input = proof.get("public_inputs", [None, None])[0]
            proof_prime = proof.get("public_inputs", [None, None])[1]
            
            if proof_public_input is None or proof_prime is None:
                return False
                
            if proof_prime != self.prime:
                return False
                
            # In a real implementation, we would:
            # 1. Use the verifier key to verify the proof
            # 2. Check that the public input matches
            
            # For this demo, we'll check the structure and that the witness squares to the public input
            proof_data = proof.get("proof", {})
            witness = proof_data.get("witness")
            
            if witness is None:
                return False
                
            # Verify that witness^2 ≡ public_input (mod prime)
            return (witness * witness) % self.prime == public_input % self.prime
        except Exception as e:
            print(f"Error verifying proof: {e}")
            return False


class SimpleMathZKPBackend:
    """
    A ZKP backend for simple mathematical statements using zkpy.
    Currently supports square root proofs.
    """
    
    def __init__(self):
        if not ZKPY_AVAILABLE:
            raise ImportError("zkpy is not available. Install with: pip install zkpy")
        
        self.sqrt_circuit = SquareRootCircuit(prime=101)
        self.initialized = True
    
    def setup(self) -> bool:
        """Initialize the backend."""
        return self.initialized
    
    def create_commitment(self, data: bytes) -> ZKPCommitment:
        """
        Create a commitment to data.
        
        For this simple backend, we'll just hash the data and use the hash as the commitment.
        The blinding factor is random.
        Note: This doesn't use the ZKP capabilities for the commitment itself,
        but shows how we could integrate.
        """
        blinding_factor = secrets.token_bytes(16)
        # Simple commitment: HASH(data + blinding_factor)
        import hashlib
        commitment_hash = hashlib.sha256(data + blinding_factor).hexdigest()
        
        return ZKPCommitment(
            commitment=commitment_hash,
            blinding_factor=blinding_factor.hex(),
            commitment_type="simple_hash"
        )
    
    def generate_proof(self, 
                      witness: Dict[str, Any], 
                      statement: Dict[str, Any]) -> Optional[ZKPProof]:
        """
        Generate a ZKP for a simple mathematical statement.
        
        Expected statement types:
        - {"type": "square_root", "y": int, "prime": int}
        
        Expected witness format for square_root:
        {
            "type": "square_root",
            "x": int  # The witness such that x^2 ≡ y (mod prime)
        }
        """
        if not self.initialized:
            return None
            
        try:
            stmt_type = statement.get("type")
            
            if stmt_type == "square_root":
                y = statement.get("y")
                prime = statement.get("prime", 101)
                
                if y is None:
                    return None
                
                witness_x = witness.get("x")
                if witness_x is None:
                    return None
                
                # Check that the witness satisfies the statement
                if (witness_x * witness_x) % prime != y % prime:
                    return None
                
                # In a real implementation, we would use the circuit to generate a proper ZKP
                # For this demo, we'll create a proof that includes the witness (not zero-knowledge)
                # but shows the interface works
                
                proof_data = {
                    "type": "square_root",
                    "witness": witness_x,
                    "statement": f"x^2 ≡ {y} (mod {prime})",
                    "zkp_data": secrets.token_hex(16)  # Simulated ZKP data
                }
                
                return ZKPProof(
                    proof=json.dumps(proof_data),
                    public_inputs={
                        "type": "square_root",
                        "y": y % prime,
                        "prime": prime
                    },
                    proof_type="simple_math_zkp",
                    verification_key="simulated_verifier_key"
                )
            
            return None
        except Exception as e:
            print(f"Error generating ZKP: {e}")
            return None
    
    def verify_proof(self, 
                    proof: ZKPProof, 
                    statement: Dict[str, Any]) -> bool:
        """Verify a ZKP for a simple mathematical statement."""
        if not self.initialized or not proof:
            return False
            
        try:
            stmt_type = statement.get("type")
            
            if stmt_type == "square_root":
                y = statement.get("y")
                prime = statement.get("prime", 101)
                
                if y is None:
                    return False
                
                # Parse the proof
                proof_data = json.loads(proof.proof)
                
                # Check statement type matches
                if proof_data.get("type") != "square_root":
                    return False
                
                # Check public inputs match
                pub_inputs = proof.public_inputs
                if pub_inputs.get("y") != y % prime or pub_inputs.get("prime") != prime:
                    return False
                
                # Extract witness and verify
                witness_x = proof_data.get("witness")
                if witness_x is None:
                    return False
                
                # Verify the witness satisfies the statement
                return (witness_x * witness_x) % prime == y % prime
            
            return False
        except Exception as e:
            print(f"Error verifying ZKP: {e}")
            return False


# Factory function
def get_math_zkp_backend() -> Optional[ZKPBackend]:
    """Get a simple math ZKP backend if zkpy is available."""
    if not ZKPY_AVAILABLE:
        return None
    try:
        return SimpleMathZKPBackend()
    except Exception:
        return None


# Demo function
def demo_math_zkp_backend():
    """Demonstrate the simple math ZKP backend."""
    print("=== Simple Math ZKP Backend Demo ===")
    print()
    
    # Try to get the backend
    backend = get_math_zkp_backend()
    
    if backend is None:
        print("Math ZKP backend not available (zkpy missing or error).")
        print("Falling back to simulated backend for demonstration.")
        from abraxas.zkp.zkp_interface import SimulatedZKPBackend
        backend = SimulatedZKPBackend()
    
    if not backend.setup():
        print("Failed to initialize ZKP backend.")
        return
    
    print(f"ZKP Backend Initialized: {type(backend).__name__}")
    print(f"ZKP Available: {ZKPY_AVAILABLE}")
    print()
    
    # Example 1: Create a commitment
    test_data = b"Evidence data for ZKP demo"
    commitment = backend.create_commitment(test_data)
    print("Generated Commitment:")
    print(f"  Commitment: {commitment.commitment}")
    print(f"  Blinding Factor: {commitment.blinding_factor}")
    print()
    
    # Example 2: Generate and verify a square root proof
    print("--- Square Root Proof Demo ---")
    # We want to prove knowledge of x such that x^2 ≡ y (mod 101)
    # Let's pick x = 10, then y = 100 mod 101 = 100
    x = 10
    prime = 101
    y = (x * x) % prime  # 100
    
    witness = {
        "type": "square_root",
        "x": x
    }
    
    statement = {
        "type": "square_root",
        "y": y,
        "prime": prime
    }
    
    print(f"Statement: {x}^2 ≡ {y} (mod {prime})")
    print(f"Witness: x = {x}")
    print()
    
    proof = backend.generate_proof(witness, statement)
    
    if proof:
        print("Generated Proof:")
        print(f"  Proof: {proof.proof[:100]}...")  # Truncate for display
        print(f"  Proof Type: {proof.proof_type}")
        print(f"  Public Inputs: {proof.public_inputs}")
        print()
        
        # Verify the proof
        is_valid = backend.verify_proof(proof, statement)
        print(f"Proof Verification: {'VALID' if is_valid else 'INVALID'}")
        print()
        
        # Try with wrong witness (should fail)
        wrong_witness = {
            "type": "square_root",
            "x": x + 1  # 11, which squared is 121 mod 101 = 20, not 100
        }
        
        wrong_proof = backend.generate_proof(wrong_witness, statement)
        if wrong_proof:
            is_valid_wrong = backend.verify_proof(wrong_proof, statement)
            print(f"Wrong Witness Proof Verification: {'VALID' if is_valid_wrong else 'INVALID'}")
            print("(This should be INVALID)")
        else:
            print("Could not generate proof for wrong witness (as expected)")
        print()
    else:
        print("Failed to generate proof.")
        print()
    
    print("=== Demo Complete ===")


if __name__ == "__main__":
    demo_math_zkp_backend()
