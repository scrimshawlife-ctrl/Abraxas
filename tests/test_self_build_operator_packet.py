import json
from pathlib import Path

from abraxas.operator.self_build_operator_packet import run_self_build_operator_packet


def test_operator_packet():
    out = run_self_build_operator_packet()
    assert out['schema_version'] == 'SelfBuildOperatorPacket.v1'
    assert 'semantic_lineage' in out
    sl = out['semantic_lineage']
    assert {'status', 'warning_count', 'missing_envelope_count', 'broken_parent_reference_count', 'orphan_contract_count'}.issubset(sl.keys())
    assert 'out/semantic/semantic_lineage_report.latest.json' in out['artifact_pointers']
    assert 'readiness_policy_hash' in out
    assert 'readiness_policy_trends' in out
    pts = out['readiness_policy_trends']
    assert {'status','active_policy_hash','policy_hash_change_count','persistent_blockers','readiness_status_drift_under_same_policy'}.issubset(pts.keys())
    assert 'out/registry/readiness_policy_trends.latest.json' in out['artifact_pointers']

    assert 'operator_decision_summary' in out
    ds = out['operator_decision_summary']
    assert {'decision_state','reason','confidence','blocking_domains','suggested_command','source_hashes'}.issubset(ds.keys())
    assert isinstance(ds['suggested_command'], (str, type(None)))
    assert 0 <= ds['confidence'] <= 1
    assert out['authority']['mutation'] is False
    assert out['authority']['promotion'] is False
    assert out['authority']['execution'] is False


def test_blocked_readiness_yields_hold_or_investigate(tmp_path):
    readiness_path = Path('out/registry/self_build_readiness_gate.latest.json')
    original = readiness_path.read_text(encoding='utf-8')
    try:
        r = json.loads(original)
        r['status'] = 'NOT_READY'
        r['blockers'] = ['lineage_no_broken_links']
        readiness_path.write_text(json.dumps(r), encoding='utf-8')
        out = run_self_build_operator_packet()
        assert out['operator_decision_summary']['decision_state'] in {'HOLD', 'INVESTIGATE'}
    finally:
        readiness_path.write_text(original, encoding='utf-8')


def test_approval_only_with_approve_one_yields_approve_one(tmp_path):
    readiness_path = Path('out/registry/self_build_readiness_gate.latest.json')
    recs_path = Path('out/registry/self_build_operator_action_recommendations.latest.json')
    r0 = readiness_path.read_text(encoding='utf-8')
    a0 = recs_path.read_text(encoding='utf-8')
    try:
        r = json.loads(r0)
        r['status'] = 'WAITING_FOR_APPROVAL'
        r['blockers'] = []
        readiness_path.write_text(json.dumps(r), encoding='utf-8')
        a = json.loads(a0)
        if isinstance(a.get('actions'), list) and a['actions']:
            a['actions'][0]['action_type'] = 'APPROVE_ONE'
            a['actions'][0]['action_id'] = 'ACT-001'
        recs_path.write_text(json.dumps(a), encoding='utf-8')
        out = run_self_build_operator_packet()
        assert out['operator_decision_summary']['decision_state'] == 'APPROVE_ONE'
    finally:
        readiness_path.write_text(r0, encoding='utf-8')
        recs_path.write_text(a0, encoding='utf-8')
