from __future__ import annotations

import os
import tempfile

from abraxas.oracle.v2.metrics_evidence import evidence_overflow_metrics
from abraxas.oracle.v2.collect import collect_v2_checks


def _env_with_paths(paths):
    return {"oracle_signal": {"evidence": {"paths": dict(paths)}}}


def test_overflow_rate_zero_when_under_budget():
    with tempfile.TemporaryDirectory() as td:
        f1 = os.path.join(td, "a.bin")
        with open(f1, "wb") as f:
            f.write(b"x" * 100)
        env = _env_with_paths({"a": f1})
        m = evidence_overflow_metrics(env, budget_bytes=1000)
        assert m["total_evidence_bytes"] == 100
        assert m["overflow_bytes"] == 0
        assert m["overflow_rate"] == 0.0


def test_overflow_rate_capped_at_one():
    with tempfile.TemporaryDirectory() as td:
        f1 = os.path.join(td, "a.bin")
        with open(f1, "wb") as f:
            f.write(b"x" * 5000)
        env = _env_with_paths({"a": f1})
        m = evidence_overflow_metrics(env, budget_bytes=1000)
        assert m["total_evidence_bytes"] == 5000
        assert m["overflow_bytes"] == 4000
        assert m["overflow_rate"] == 1.0


def test_collect_checks_derives_overflow_when_paths_present():
    with tempfile.TemporaryDirectory() as td:
        f1 = os.path.join(td, "a.bin")
        with open(f1, "wb") as f:
            f.write(b"x" * 2000)
        env = _env_with_paths({"a": f1})
        checks = collect_v2_checks(envelope=env, evidence_budget_bytes=1000)
        assert "evidence_bundle_overflow_rate" in checks
        assert checks["evidence_bundle_overflow_rate"] == 1.0


def test_collect_checks_keeps_default_when_no_evidence():
    env = {"oracle_signal": {}}
    checks = collect_v2_checks(envelope=env, evidence_budget_bytes=1000)
    assert checks["evidence_bundle_overflow_rate"] == 0.0
