import json
import subprocess
import sys


def test_run_proof_returns_not_computable_for_unregistered_subsystem():
    cp = subprocess.run(
        [sys.executable, "scripts/run_proof.py", "--subsystem", "not_in_registry_subsystem"],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 2
    payload = json.loads(cp.stdout)
    assert payload["status"] == "NOT_COMPUTABLE"
    assert payload["reason"] == "subsystem_not_registered_in_expected_subsystems"
    assert payload["registrationReceipt"]["label"] == "subsystem_registration_check"
    assert payload["registrationReceipt"]["status"] == "BLOCKED"
    assert payload["artifacts"] == {}
    assert payload["presentReceipts"] == []
