#!/usr/bin/env python3
"""
Run arbitration policy experiments as described in experiment_design.md
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from abraxas.governance.production import ProductionOrchestrator
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep
from abraxas.governance.policy import DefaultArbitrationPolicy, ArbitrationPolicyConfig
from abraxas.governance.six_gate import SixGateGovernor
import statistics
from collections import defaultdict
import json

def create_test_claims():
    """Create a set of test claims as described in the experiment."""
    claims = []
    
    # 10 easily verifiable facts
    for i in range(10):
        claims.append({
            "claim": f"Easily verifiable fact {i}: Water is H2O",
            "expected_difficulty": "easy",
            "expected_verdict": "TRUE"  # We'll treat as true for simplicity
        })
    
    # 10 moderately complex claims
    for i in range(10):
        claims.append({
            "claim": f"Moderately complex claim {i}: Machine learning improves diagnostic accuracy in radiology",
            "expected_difficulty": "moderate",
            "expected_verdict": "TRUE"
        })
    
    # 10 ambiguous claims
    for i in range(10):
        claims.append({
            "claim": f"Ambiguous claim {i}: Artificial intelligence will surpass human intelligence by 2050",
            "expected_difficulty": "ambiguous",
            "expected_verdict": "UNCERTAIN"
        })
    
    # 10 false claims
    for i in range(10):
        claims.append({
            "claim": f"False claim {i}: The Earth is flat",
            "expected_difficulty": "false",
            "expected_verdict": "FALSE"
        })
    
    # 10 complex scientific claims
    for i in range(10):
        claims.append({
            "claim": f"Complex scientific claim {i}: Quantum entanglement allows faster-than-light communication",
            "expected_difficulty": "complex",
            "expected_verdict": "FALSE"  # Actually false, but note: quantum entanglement doesn't allow FTL communication
        })
    
    return claims

def create_evidence_envelope(claim_text, engine_name="test_engine", confidence=0.8):
    """Create a simple evidence envelope for testing."""
    # Create a simple candidate output
    candidate_output = CandidateOutput(
        answer="TRUE" if "true" in claim_text.lower() or "yes" in claim_text.lower() or "is" in claim_text.lower() else "FALSE",
        confidence=confidence,
        reasoning_trace=f"Simple reasoning for: {claim_text}",
        relation_steps=[
            RelationStep(
                relation="simple_check",
                subject=claim_text,
                object="TRUE" if "true" in claim_text.lower() or "yes" in claim_text.lower() or "is" in claim_text.lower() else "FALSE",
                result="Based on simple string matching",
                confidence=0.7
            )
        ]
    )
    
    envelope = EvidenceEnvelope(
        engine=engine_name,
        engine_version="1.0",
        model_identity="test_model",
        request_id=f"test-{hash(claim_text)}",
        claim=claim_text,
        candidate_outputs=[candidate_output],
        evidence_type=EvidenceType.RELATIONAL_REASONING,
        confidence=confidence,
        uncertainty=1.0 - confidence,
        provenance={"test": True}
    )
    return envelope

def run_policy_experiment(policy_config, claims, policy_name):
    """Run a set of claims through the arbiter with a given policy."""
    print(f"\n=== Testing policy: {policy_name} ===")
    print(f"Policy config: accept={policy_config.accept_threshold}, verify={policy_config.verify_threshold}, recompute={policy_config.recompute_threshold}")
    
    # Create orchestrator with the given policy
    orchestrator = ProductionOrchestrator()
    # Override the policy in the orchestrator's arbiter
    orchestrator.arbiter.policy = DefaultArbitrationPolicy(policy_config)
    
    results = []
    decision_counts = defaultdict(int)
    
    for i, claim_data in enumerate(claims):
        claim_text = claim_data["claim"]
        # Create evidence for this claim
        evidence = create_evidence_envelope(claim_text, confidence=0.75)  # Fixed confidence for testing
        
        try:
            # Process the evidence
            result = orchestrator.process_evidence(evidence)
            
            decision = result.get('decision', 'UNKNOWN')
            decision_counts[decision] += 1
            
            results.append({
                "claim": claim_text,
                "expected_difficulty": claim_data["expected_difficulty"],
                "expected_verdict": claim_data["expected_verdict"],
                "decision": decision,
                "confidence": evidence.confidence,
                "governance_score": result.get('governance_score', 0.0),
                "processing_time": result.get('processing_time', 0.0)
            })
            
            if (i+1) % 10 == 0:
                print(f"  Processed {i+1}/{len(claims)} claims")
                
        except Exception as e:
            print(f"  Error processing claim {i}: {e}")
            results.append({
                "claim": claim_text,
                "expected_difficulty": claim_data["expected_difficulty"],
                "expected_verdict": claim_data["expected_verdict"],
                "decision": "ERROR",
                "error": str(e)
            })
    
    # Print summary
    print(f"  Decision distribution: {dict(decision_counts)}")
    total = len(claims)
    for decision, count in decision_counts.items():
        print(f"    {decision}: {count}/{total} ({count/total*100:.1f}%)")
    
    return {
        "policy_name": policy_name,
        "policy_config": {
            "accept": policy_config.accept_threshold,
            "verify": policy_config.verify_threshold,
            "recompute": policy_config.recompute_threshold
        },
        "decision_counts": dict(decision_counts),
        "results": results
    }

def main():
    print("Starting Abraxas Arbitration Policy Experiments")
    print("=" * 50)
    
    # Create test claims
    claims = create_test_claims()
    print(f"Created {len(claims)} test claims")
    
    # Define policy configurations from the experiment
    policies = [
        ("Baseline", ArbitrationPolicyConfig(accept_threshold=0.85, verify_threshold=0.60, recompute_threshold=0.40)),
        ("Strict", ArbitrationPolicyConfig(accept_threshold=0.95, verify_threshold=0.70, recompute_threshold=0.50)),
        ("Lenient", ArbitrationPolicyConfig(accept_threshold=0.75, verify_threshold=0.50, recompute_threshold=0.30)),
        ("High Verify", ArbitrationPolicyConfig(accept_threshold=0.85, verify_threshold=0.80, recompute_threshold=0.40))
    ]
    
    all_results = []
    
    for policy_name, policy_config in policies:
        result = run_policy_experiment(policy_config, claims, policy_name)
        all_results.append(result)
    
    # Print comparative summary
    print("\n" + "=" * 50)
    print("COMPARATIVE SUMMARY")
    print("=" * 50)
    
    for result in all_results:
        print(f"\n{result['policy_name']}:")
        print(f"  Config: accept={result['policy_config']['accept']}, verify={result['policy_config']['verify']}, recompute={result['policy_config']['recompute']}")
        print(f"  Decisions: {result['decision_counts']}")
    
    # Save results to file
    output_file = "/Users/appliedalchemylabs/Abraxas/research/arbitration_policies/experiment_results.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    print("Experiments completed.")

if __name__ == "__main__":
    main()