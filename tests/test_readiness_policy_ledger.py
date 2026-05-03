import json
from pathlib import Path
import subprocess


LEDGER = Path("out/registry/readiness_policy_ledger.latest.json")


def _run_readiness_and_ledger():
    subprocess.run(["python", "scripts/run_self_build_readiness_gate.py"], check=True)
    subprocess.run(["python", "scripts/run_readiness_policy_ledger.py"], check=True)


def test_missing_readiness_fails_closed(tmp_path):
    readiness = Path("out/registry/self_build_readiness_gate.latest.json")
    backup = readiness.read_text(encoding="utf-8") if readiness.exists() else None
    if readiness.exists():
        readiness.unlink()
    try:
        subprocess.run(["python", "scripts/run_readiness_policy_ledger.py"], check=True)
        out = json.loads(LEDGER.read_text(encoding="utf-8"))
        assert out["status"] == "NOT_COMPUTABLE"
    finally:
        if backup is not None:
            readiness.write_text(backup, encoding="utf-8")


def test_append_behavior_and_required_fields():
    if LEDGER.exists():
        LEDGER.unlink()
    _run_readiness_and_ledger()
    first = json.loads(LEDGER.read_text(encoding="utf-8"))
    _run_readiness_and_ledger()
    second = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert len(second["entries"]) == len(first["entries"]) + 1
    last = second["entries"][-1]
    for key in ["policy_hash", "policy_schema_version", "policy_path", "policy_fields_used", "readiness_status", "readiness_hash", "blockers", "canonical_hash"]:
        assert key in last


def test_deterministic_canonical_hash_for_same_state():
    if LEDGER.exists():
        LEDGER.unlink()
    _run_readiness_and_ledger()
    a = json.loads(LEDGER.read_text(encoding="utf-8"))
    if LEDGER.exists():
        LEDGER.unlink()
    _run_readiness_and_ledger()
    b = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert a["entries"][0]["canonical_hash"] == b["entries"][0]["canonical_hash"]
