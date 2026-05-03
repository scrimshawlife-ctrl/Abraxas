import json
from pathlib import Path
import subprocess


def _write_ledger(entries):
    payload = {
        "schema_version": "ReadinessPolicyLedger.v1",
        "status": "LEDGER_READY",
        "entries": entries,
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    Path("out/registry").mkdir(parents=True, exist_ok=True)
    Path("out/registry/readiness_policy_ledger.latest.json").write_text(json.dumps(payload), encoding="utf-8")


def test_not_computable_when_missing_ledger(tmp_path):
    p = Path("out/registry/readiness_policy_ledger.latest.json")
    backup = p.read_text(encoding="utf-8") if p.exists() else None
    if p.exists():
        p.unlink()
    try:
        subprocess.run(["python", "scripts/run_readiness_policy_trends.py"], check=True)
        out = json.loads(Path("out/registry/readiness_policy_trends.latest.json").read_text())
        assert out["status"] == "NOT_COMPUTABLE"
    finally:
        if backup is not None:
            p.write_text(backup, encoding="utf-8")


def test_trend_fields_present():
    _write_ledger([
        {"policy_hash": "A", "readiness_status": "NOT_READY", "blockers": ["b1"]},
        {"policy_hash": "A", "readiness_status": "WAITING_FOR_APPROVAL", "blockers": ["b1"]},
        {"policy_hash": "B", "readiness_status": "NOT_READY", "blockers": ["b1", "b2"]},
        {"policy_hash": "B", "readiness_status": "NOT_READY", "blockers": ["b1"]},
    ])
    subprocess.run(["python", "scripts/run_readiness_policy_trends.py"], check=True)
    out = json.loads(Path("out/registry/readiness_policy_trends.latest.json").read_text())
    assert out["status"] == "TRENDS_READY"
    assert "policy_hash_changes" in out
    assert "readiness_status_drift_under_same_policy" in out
    assert "persistent_blockers" in out
    assert "blocker_frequency_patterns" in out
    assert "policy_vs_state_causality" in out
