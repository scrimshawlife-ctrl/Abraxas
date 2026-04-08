import json
import subprocess
import sys
from pathlib import Path


def test_capture_guardrail_receipts_bundle(tmp_path: Path):
    out = tmp_path / "receipts.json"
    cp = subprocess.run(
        [
            sys.executable,
            "scripts/capture_guardrail_receipts.py",
            "--subsystem",
            "oracle_signal_layer_v2",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0
    payload = json.loads(out.read_text())
    assert payload["schema_version"] == 1
    assert payload["receipt_bundle_id"]
    assert "checks" in payload
    assert "receipts" in payload
