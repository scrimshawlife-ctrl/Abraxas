from pathlib import Path

from abraxas.governance.drift_check import run_drift_check


def test_drift_check_deterministic_output():
    repo_root = Path(__file__).parent.parent
    canon_path = repo_root / ".abraxas" / "canon_state.v0.yaml"

    exit_code_1, output_1 = run_drift_check(
        repo_root=repo_root, canon_path=canon_path
    )
    exit_code_2, output_2 = run_drift_check(
        repo_root=repo_root, canon_path=canon_path
    )

    assert exit_code_1 == 0
    assert exit_code_2 == 0
    assert output_1 == output_2


def test_drift_check_missing_file(tmp_path):
    missing_path = tmp_path / "canon_state.v0.yaml"
    exit_code, output = run_drift_check(
        repo_root=tmp_path, canon_path=missing_path
    )

    assert exit_code != 0
    assert "Canon state file not found" in output


def test_drift_check_invalid_enum(tmp_path):
    canon_path = tmp_path / "canon_state.v0.yaml"
    canon_path.write_text(
        "\n".join(
            [
                "canon_state_version: v0",
                "system_name: TestSystem",
                "repo_version: \"0.0.0\"",
                "governance_flags:",
                "  incremental_patch_only: true",
                "subsystems:",
                "  - key: core",
                "    path: .",
                "    lane: invalid-lane",
                "    implementation_state: invalid-state",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code, output = run_drift_check(repo_root=tmp_path, canon_path=canon_path)

    assert exit_code != 0
    assert "invalid_lane" in output
    assert "invalid_implementation_state" in output
