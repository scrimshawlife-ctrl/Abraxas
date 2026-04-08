import json
import subprocess
import sys
from pathlib import Path


def test_validate_guardrail_receipts_passes_for_generated_bundle(tmp_path: Path):
    bundle = tmp_path / "guardrail_receipts.json"
    artifact = tmp_path / "guardrail_validator.json"

    capture = subprocess.run(
        [
            sys.executable,
            "scripts/capture_guardrail_receipts.py",
            "--subsystem",
            "oracle_signal_layer_v2",
            "--out",
            str(bundle),
        ],
        capture_output=True,
        text=True,
    )
    assert capture.returncode == 0

    validate = subprocess.run(
        [
            sys.executable,
            "scripts/validate_guardrail_receipts.py",
            "--bundle",
            str(bundle),
            "--out",
            str(artifact),
        ],
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 0
    payload = json.loads(artifact.read_text())
    assert payload["status"] == "VALID"
    assert payload["checkedReceiptCount"] >= 1


def test_validate_guardrail_receipts_blocks_tampered_bundle(tmp_path: Path):
    bundle = tmp_path / "guardrail_receipts.json"
    artifact = tmp_path / "guardrail_validator.json"

    capture = subprocess.run(
        [
            sys.executable,
            "scripts/capture_guardrail_receipts.py",
            "--subsystem",
            "oracle_signal_layer_v2",
            "--out",
            str(bundle),
        ],
        capture_output=True,
        text=True,
    )
    assert capture.returncode == 0

    payload = json.loads(bundle.read_text())
    payload["receipts"].append("forged_receipt")
    bundle.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    validate = subprocess.run(
        [
            sys.executable,
            "scripts/validate_guardrail_receipts.py",
            "--bundle",
            str(bundle),
            "--out",
            str(artifact),
        ],
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 1
    artifact_payload = json.loads(artifact.read_text())
    assert artifact_payload["status"] == "INVALID"
    assert artifact_payload["errors"]
