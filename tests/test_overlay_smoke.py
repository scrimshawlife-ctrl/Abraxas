import json
import subprocess
from pathlib import Path

def test_overlay_runs():
    # Get repository root (parent of tests/)
    repo_root = Path(__file__).resolve().parents[1]

    req = {
        "overlay": "abraxas",
        "version": "2.1",
        "phase": "OPEN",
        "request_id": "test-1",
        "timestamp_ms": 1,
        "payload": {"prompt": "hello", "intent": "smoke"},
    }

    p = subprocess.run(
        ["python", "-m", "abraxas.overlay.run"],
        input=json.dumps(req).encode("utf-8"),
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=2.0,
    )

    assert p.returncode == 0
    out = json.loads(p.stdout.decode("utf-8"))
    assert out["ok"] is True
    assert out["phase"] == "OPEN"
