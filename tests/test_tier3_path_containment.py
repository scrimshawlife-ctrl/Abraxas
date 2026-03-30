from __future__ import annotations

from types import SimpleNamespace

from abx.cli import acceptance_cmd


def test_acceptance_cmd_refuses_by_default(monkeypatch, capsys) -> None:
    monkeypatch.delenv("ABX_ALLOW_SHADOW_ACCEPTANCE", raising=False)

    code = acceptance_cmd()
    captured = capsys.readouterr()

    assert code == 2
    assert "SHADOW_DIAGNOSTIC" in captured.err
    assert "run_execution_attestation.py" in captured.err


def test_acceptance_cmd_allows_shadow_only_with_explicit_override(monkeypatch) -> None:
    monkeypatch.setenv("ABX_ALLOW_SHADOW_ACCEPTANCE", "1")

    def _fake_run(*_args, **_kwargs):
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("abx.cli.subprocess.run", _fake_run)

    assert acceptance_cmd() == 0
