import json
import subprocess
import sys
from pathlib import Path


def test_validate_mircl_v1_artifact_detects_tamper(tmp_path: Path):
    artifact = tmp_path / "artifact.json"
    artifact.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "subsystem": "mircl_v1",
                "lane": "shadow",
                "request_id": "MIRCL-REQ-0002",
                "advisory_id": "bad",
                "source_prompt": "Prompt",
                "advisory_text": "MIRCL shadow advisory for request MIRCL-REQ-0002: Prompt",
                "context_tags": ["shadow"],
                "status": "shadow_advisory_emitted",
            }
        ),
        encoding="utf-8",
    )

    out = tmp_path / "validator.json"
    cp = subprocess.run(
        [
            sys.executable,
            "scripts/validate_mircl_v1_artifact.py",
            "--artifact",
            str(artifact),
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 1
    payload = json.loads(out.read_text())
    assert payload["status"] == "INVALID"
