from __future__ import annotations

from pathlib import Path

from scripts.run_release_readiness import run_release_readiness


def test_release_readiness_report_has_expected_schema(monkeypatch, tmp_path: Path) -> None:
    for rel in [
        "README.md",
        "docs/CANONICAL_RUNTIME.md",
        "docs/VALIDATION_AND_ATTESTATION.md",
        "docs/SUBSYSTEM_INVENTORY.md",
        "docs/RELEASE_READINESS.md",
    ]:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("ok", encoding="utf-8")

    class Proc:
        def __init__(self, code: int = 0, stderr: str = "", stdout: str = ""):
            self.returncode = code
            self.stderr = stderr
            self.stdout = stdout

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        joined = " ".join(cmd)
        if "run_execution_attestation.py" in joined:
            return Proc(1, "policy-gate blocked")
        return Proc(0, "", "ok")

    monkeypatch.setattr("scripts.run_release_readiness.subprocess.run", fake_run)

    report = run_release_readiness("RUN-RR-001", base_dir=tmp_path)

    assert report["schema"] == "ReleaseReadinessReport.v1"
    assert report["status"] == "READY"
    tier3 = [c for c in report["checks"] if c["name"] == "tier3_attestation"][0]
    assert tier3["outcome"] == "PASS_EXPECTED_FAIL_CLOSED"
