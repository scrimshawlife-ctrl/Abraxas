from __future__ import annotations

import json
from pathlib import Path

from scripts.run_activation_receipt_completion_pass import COMMANDS, REQUIRED_ARTIFACTS, run_completion_pass


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_completion_sealed_and_deterministic(tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(command, cwd, check):  # type: ignore[no-untyped-def]
        calls.append(command)

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr("scripts.run_activation_receipt_completion_pass.subprocess.run", _fake_run)

    for rel in REQUIRED_ARTIFACTS:
        _write(tmp_path / rel, {"status": "ok"})

    _write(
        tmp_path / "out/ledger/pse_calibration_activation_receipt.latest.json",
        {"status": "RECEIPT_SEALED", "promotion": {"eligible": True}},
    )

    first = run_completion_pass(tmp_path)
    second = run_completion_pass(tmp_path)
    assert first == second
    assert first["status"] == "COMPLETION_SEALED"
    assert first["receipt_status"] == "RECEIPT_SEALED"
    assert first["promotion_eligible"] is True
    assert calls[: len(COMMANDS)] == [entry["cmd"] for entry in COMMANDS]


def test_completion_blocked_on_missing_or_unsealed_receipt(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.run_activation_receipt_completion_pass.subprocess.run",
        lambda command, cwd, check: type("R", (), {"returncode": 0})(),
    )

    for rel in REQUIRED_ARTIFACTS[:-1]:
        _write(tmp_path / rel, {"status": "ok"})
    _write(
        tmp_path / "out/ledger/pse_calibration_activation_receipt.latest.json",
        {"status": "RECEIPT_BLOCKED", "promotion": {"eligible": False}},
    )

    report = run_completion_pass(tmp_path)
    assert report["status"] == "COMPLETION_BLOCKED"
    assert report["promotion_eligible"] is False
    assert REQUIRED_ARTIFACTS[-1] in report["missing_artifacts"]
