import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from abraxas.zkp.zkp_interface import EvidenceZKPManager
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep

def create_sample_evidence():
    return EvidenceEnvelope(
        engine="demo_engine",
        engine_version="1.0",
        model_identity="demo_model",
        request_id="demo-001",
        claim="Test claim",
        candidate_outputs=[CandidateOutput(
            answer="True",
            confidence=0.95,
            reasoning_trace="Test reasoning",
            relation_steps=[]
        )],
        evidence_type=EvidenceType.RELATIONAL_REASONING,
        confidence=0.95,
        uncertainty=0.05,
        provenance={"demo": True}
    )

manager = EvidenceZKPManager()
print(f"Manager initialized: {manager.is_initialized}")
print(f"Backend: {type(manager.zkp_backend).__name__}")

evidence = create_sample_evidence()
print(f"Evidence created: {evidence.evidence_id}")

commitment = manager.create_evidence_commitment(evidence)
print(f"Commitment: {commitment}")
if commitment is None:
    print("Commitment is None!")
    # Let's check the backend's create_commitment method directly
    from abraxas.zkp.zkp_interface import SimulatedZKPBackend
    sim = SimulatedZKPBackend()
    sim.setup()
    print(f"Sim backend initialized: {sim.initialized}")
    # Now try to create commitment with the envelope's canonical form
    import json
    canonical_json = json.dumps(evidence.to_dict(), sort_keys=True)
    print(f"Canonical JSON length: {len(canonical_json)}")
    data = canonical_json.encode('utf-8')
    print(f"Data length: {len(data)}")
    commitment2 = sim.create_commitment(data)
    print(f"Direct commitment: {commitment2}")
else:
    print(f"Commitment created: {commitment.commitment}")