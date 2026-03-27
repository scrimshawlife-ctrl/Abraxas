from __future__ import annotations

from types import SimpleNamespace

import pytest

import scripts.dozen_run_gate_runtime as legacy_gate_runtime
import scripts.n_run_gate_runtime as gate_runtime


class _Capture:
    def __init__(self) -> None:
        self.note: str | None = None


def test_main_rejects_runs_below_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["dozen_run_gate_runtime", "--artifacts_dir", "out/x", "--runs", "0"],
    )

    with pytest.raises(SystemExit) as exc:
        gate_runtime.main()

    assert exc.value.code == 2


def test_main_persists_run_count_note_on_success(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    capture = _Capture()

    def fake_gate(**kwargs):
        return SimpleNamespace(
            ok=True,
            expected_sha256="trend-hash",
            sha256s=["trend-hash"] * 10,
            expected_runheader_sha256="header-hash",
            runheader_sha256s=["header-hash"] * 10,
            first_mismatch_run=None,
            divergence=None,
        )

    def fake_write_run_stability(*, artifacts_dir, run_id, gate_result, note):
        capture.note = note
        return f"{artifacts_dir}/runs/{run_id}.runstability.json", "stab-sha"

    monkeypatch.setattr(gate_runtime, "dozen_run_tick_invariance_gate", fake_gate)
    monkeypatch.setattr(gate_runtime, "write_run_stability", fake_write_run_stability)
    monkeypatch.setattr(
        gate_runtime,
        "write_stability_ref",
        lambda **kwargs: (f"{kwargs['artifacts_dir']}/runs/{kwargs['run_id']}.stability_ref.json", "ref-sha"),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "dozen_run_gate_runtime",
            "--artifacts_dir",
            str(tmp_path),
            "--run_id",
            "gate10",
            "--runs",
            "10",
        ],
    )

    rc = gate_runtime.main()

    assert rc == 0
    assert capture.note == "10-run gate pass"


def test_legacy_shim_exports_canonical_main() -> None:
    assert legacy_gate_runtime.main is gate_runtime.main
