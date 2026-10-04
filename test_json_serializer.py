import sys
sys.path.insert(0, '.')
from abraxas.yggdrasil.memory import CypherMemoryLayer, MemoryRecord
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep
from datetime import datetime, timezone
import json

# Test if the JSON serializer works
print('Testing JSON serializer...')
try:
    # Create a simple evidence envelope
    envelope = EvidenceEnvelope(
        engine='test_engine',
        engine_version='1.0',
        model_identity='test_model',
        request_id='test-001',
        claim='Test claim',
        candidate_outputs=[CandidateOutput(
            answer='True',
            confidence=0.95,
            reasoning_trace='Test reasoning',
            relation_steps=[RelationStep(
                relation='test_relation',
                subject='test_subject',
                object='test_object',
                result='test_result',
                confidence=0.9
            )]
        )],
        evidence_type=EvidenceType.RELATIONAL_REASONING,
        confidence=0.95,
        uncertainty=0.05,
        provenance={'test': True}
    )
    
    # Test storing and retrieving
    memory = CypherMemoryLayer()
    memory.initialize()
    
    record_id = memory.store_evidence(envelope)
    print(f'Stored evidence with ID: {record_id}')
    
    retrieved = memory.retrieve_evidence(record_id)
    print('Retrieved evidence successfully')
    
    # Test JSON serialization directly
    test_data = {
        'enum_val': EvidenceType.RELATIONAL_REASONING,
        'datetime_val': datetime.now(timezone.utc),
        'nested': {
            'evidence': envelope.to_dict() if hasattr(envelope, 'to_dict') else str(envelope)
        }
    }
    
    json_str = json.dumps(test_data, default=memory._json_serializer)
    print('JSON serialization successful')
    print(f'Serialized length: {len(json_str)} characters')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()