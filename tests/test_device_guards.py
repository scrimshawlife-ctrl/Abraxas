from __future__ import annotations

from abraxas.runes.operators.no_auto_tune import apply_no_auto_tune
from abraxas.runes.operators.active_pointer_atomic import apply_active_pointer_atomic


def test_no_auto_tune_guard() -> None:
    result = apply_no_auto_tune()
    assert result["selection_only"] is True


def test_active_pointer_atomic(tmp_path) -> None:
    path = tmp_path / "ACTIVE"
    result = apply_active_pointer_atomic(path=str(path))
    assert result["atomic_ready"] is True
