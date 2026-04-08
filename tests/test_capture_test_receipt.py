import json
import subprocess
import sys
from pathlib import Path


def test_capture_test_receipt_with_subset(tmp_path: Path):
    out = tmp_path / "test_receipt.json"
    cp = subprocess.run(
        [
            sys.executable,
            "scripts/capture_test_receipt.py",
            "--out",
            str(out),
            "--tests",
            "tests/test_preflight.py",
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0
    payload = json.loads(out.read_text())
    assert payload["label"] == "deterministic_test_pass"
