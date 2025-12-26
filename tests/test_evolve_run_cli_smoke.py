from __future__ import annotations

import subprocess


def test_evolve_run_help():
    proc = subprocess.run(
        ["python", "-m", "abx.evolve_run", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "evolve_run" in (proc.stdout or "")
