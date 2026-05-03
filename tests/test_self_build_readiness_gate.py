import json
from pathlib import Path

from abraxas.registry.self_build_readiness_gate import run_self_build_readiness_gate


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def test_readiness_gate_has_lineage_gates():
    out = run_self_build_readiness_gate()
    assert out['schema_version'] == 'SelfBuildReadinessGate.v1'
    assert 'require_lineage_report' in out['gates']
    assert 'lineage_status_ready' in out['gates']
    assert 'lineage_no_broken_links' in out['gates']
    assert 'lineage_warning_count_below_threshold' in out['gates']
    assert out['authority']['mutation'] is False
    assert out['authority']['promotion'] is False
    assert out['authority']['execution'] is False
    assert 'policy_hash' in out
    assert out.get('policy_path') == '.aal/readiness_policy.v1.yaml'
    assert 'policy_fields_used' in out


def test_readiness_gate_broken_lineage_blocks():
    _write('out/semantic/semantic_lineage_report.latest.json', {
        'schema_version': 'SemanticLineageReport.v1',
        'status': 'LINEAGE_REPORT_READY',
        'warnings': ['broken_parent_reference:scoring']
    })
    out = run_self_build_readiness_gate()
    assert out['status'] == 'NOT_READY'
    assert 'lineage_no_broken_links' in out['blockers']
