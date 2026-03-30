from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts import run_promotion_pack


def test_run_promotion_pack_refuses_by_default(monkeypatch, capsys) -> None:
    monkeypatch.delenv("ABX_ALLOW_SHADOW_PROMOTION_PACK", raising=False)
    monkeypatch.setattr(run_promotion_pack.sys, "argv", ["run_promotion_pack.py"])
    code = run_promotion_pack.main()
    captured = capsys.readouterr()
    assert code == 2
    assert "SHADOW_DIAGNOSTIC" in captured.err


def test_run_promotion_pack_allows_with_explicit_override(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setenv("ABX_ALLOW_SHADOW_PROMOTION_PACK", "1")
    scenario = tmp_path / "scenario.json"
    scenario.write_text(json.dumps({"ok": True}), encoding="utf-8")

    monkeypatch.setattr(run_promotion_pack.sys, "argv", ["run_promotion_pack.py", scenario.as_posix()])
    monkeypatch.setattr(
        run_promotion_pack,
        "build_promotion_pack",
        lambda payload: SimpleNamespace(readiness="READY", payload=payload),
    )

    code = run_promotion_pack.main()
    captured = capsys.readouterr()
    assert code == 0
    assert '"readiness": "READY"' in captured.out
