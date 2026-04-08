import json
import subprocess
import sys
from pathlib import Path


def test_capture_repo_status_receipt(tmp_path: Path):
    out = tmp_path / "repo_status_receipt.json"
    cp = subprocess.run(
        [sys.executable, "scripts/capture_repo_status_receipt.py", "--out", str(out)],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0
    payload = json.loads(out.read_text())
    assert payload["label"] == "repo_status"
