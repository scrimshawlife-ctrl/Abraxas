from __future__ import annotations

import os
import tempfile

from abraxas.oracle.v2.collect import collect_v2_checks
from abraxas.oracle.v2.compliance import build_compliance_report


def test_compliance_report_includes_evidence_meta_when_present():
    """Test that compliance report includes meta.evidence when evidence exists."""
    with tempfile.TemporaryDirectory() as td:
        f1 = os.path.join(td, "a.bin")
        with open(f1, "wb") as f:
            f.write(b"x" * 2000)
        env = {"oracle_signal": {"evidence": {"paths": {"a": f1}}}}

        checks = collect_v2_checks(envelope=env, evidence_budget_bytes=1000)
        rep = build_compliance_report(checks=checks, config_hash="CFG", date_iso="2025-12-28T00:00:00Z")

        assert "meta" in rep
        assert "evidence" in rep["meta"]
        evm = rep["meta"]["evidence"]
        assert evm["total_evidence_bytes"] == 2000
        assert evm["budget_bytes"] == 1000
        assert evm["overflow_bytes"] == 1000
        assert evm["overflow_rate"] == 1.0
        # ensure the internal key was removed from checks payload
        assert "_evidence_metrics" not in rep["checks"]


def test_compliance_report_omits_meta_when_no_evidence():
    """Test that compliance report omits meta.evidence when no evidence exists."""
    env = {"oracle_signal": {}}

    checks = collect_v2_checks(envelope=env)
    rep = build_compliance_report(checks=checks, config_hash="CFG", date_iso="2025-12-28T00:00:00Z")

    # Should not have meta when no evidence
    assert "meta" not in rep
    assert "_evidence_metrics" not in rep["checks"]
