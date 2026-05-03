from pathlib import Path


def test_script_stubs_exist() -> None:
    required = [
        "scripts/run_oracle_core.py",
        "scripts/run_brier_scoring.py",
        "scripts/run_canary_review_gate.py",
    ]
    for path in required:
        assert Path(path).exists()
