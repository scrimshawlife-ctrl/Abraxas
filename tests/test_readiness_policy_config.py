import json
from pathlib import Path

import yaml

from abraxas.registry.self_build_readiness_gate import run_self_build_readiness_gate

POLICY = Path('.aal/readiness_policy.v1.yaml')


def test_valid_policy_passes():
    out = run_self_build_readiness_gate()
    assert out['schema_version'] == 'SelfBuildReadinessGate.v1'


def test_missing_policy_fails_closed(tmp_path):
    original = POLICY.read_text(encoding='utf-8')
    POLICY.unlink()
    try:
        out = run_self_build_readiness_gate()
        assert out['status'] == 'NOT_COMPUTABLE'
    finally:
        POLICY.write_text(original, encoding='utf-8')


def test_invalid_threshold_fails_closed():
    original = POLICY.read_text(encoding='utf-8')
    bad = yaml.safe_load(original)
    bad['lineage_warning_threshold'] = -1
    POLICY.write_text(yaml.safe_dump(bad), encoding='utf-8')
    try:
        out = run_self_build_readiness_gate()
        assert out['status'] == 'NOT_COMPUTABLE'
    finally:
        POLICY.write_text(original, encoding='utf-8')


def test_policy_hash_deterministic_across_runs():
    a = run_self_build_readiness_gate()
    b = run_self_build_readiness_gate()
    assert a.get("policy_hash") == b.get("policy_hash")
