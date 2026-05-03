import json
from pathlib import Path
import subprocess


from abraxas.semantic.contracts import attach_canonical_hash


def test_canary_activation_semantics_packet():
    Path('out/canary').mkdir(parents=True, exist_ok=True)
    payload = attach_canonical_hash({'schema_version':'CanaryCandidateSet.v1','candidates':[{'id':'c1','target':'svc-a','approval':'approved','safety':'ok','rollback_ready':True},{'id':'c2','target':'svc-b','approval':'approved','safety':'ok','rollback_ready':False}]})
    Path('out/canary/canary_candidate_set.latest.json').write_text(json.dumps(payload))
    subprocess.run(['python', 'scripts/run_canary_activation_semantics.py'], check=True)
    out = json.loads(Path('out/canary/canary_activation_packet.latest.json').read_text())
    assert out['schema_version'] == 'CanaryActivationPacket.v1'
    assert out['entries'][0]['status'] == 'READY_FOR_OPERATOR_REVIEW'
    assert out['entries'][1]['status'] == 'READY_FOR_OPERATOR_REVIEW'
