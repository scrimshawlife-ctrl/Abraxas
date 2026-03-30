from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_acceptance_harness_help_runs_from_non_repo_cwd(tmp_path: Path) -> None:
    script = Path("tools/acceptance/run_acceptance_suite.py").resolve()
    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "Abraxas Acceptance Test Suite" in (completed.stdout + completed.stderr)
