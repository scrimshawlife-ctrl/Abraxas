from abraxas.registry.self_build_final_stack_runner import run_self_build_final_stack_runner


def test_final_stack_runner():
    out = run_self_build_final_stack_runner()
    assert out['schema_version'] == 'SelfBuildFinalStackResult.v1'
    assert 'lineage_report_hash' in out
    assert 'lineage_status' in out
    assert 'lineage_warning_count' in out
    assert 'lineage_broken_link_count' in out
    assert 'readiness_policy_hash' in out
    assert 'policy_trends_hash' in out
    assert 'policy_trends_status' in out
    assert 'policy_hash_change_count' in out
    assert 'persistent_blocker_count' in out
    assert out['authority']['mutation'] is False
    assert out['authority']['promotion'] is False
    assert out['authority']['execution'] is False
