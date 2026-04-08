import json
import subprocess
import sys
from pathlib import Path


def test_validate_mbom_v1_artifact_detects_tamper(tmp_path: Path):
    artifact = tmp_path / "artifact.json"
    artifact.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "subsystem": "mbom_v1",
                "lane": "support",
                "request": {
                    "request_id": "MBOM-REQ-0002",
                    "lifecycle_states": {"a": "SEED"},
                    "domain_signals": ["sig-a"],
                    "resonance_score": 0.3,
                },
                "assessment": {
                    "subsystem_id": "mbom_v1",
                    "lane": "support",
                    "authority": "non-authoritative",
                    "ambiguity_score": 0.999999,
                    "ambiguity_band": "HIGH",
                    "blocked_change_classes": ["forecast_active_change", "authority_surface_drift"],
                },
                "assessment_id": "bad",
                "status": "mbom_assessment_emitted",
            }
        ),
        encoding="utf-8",
    )

    out = tmp_path / "validator.json"
    cp = subprocess.run(
        [
            sys.executable,
            "scripts/validate_mbom_v1_artifact.py",
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
