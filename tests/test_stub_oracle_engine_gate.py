from __future__ import annotations

import pytest

from abraxas.core.stub_oracle_engine import _stub_engine_adapter, run_oracle_engine
from abraxas.io.config import OverlaysConfig, UserConfig


class _Inputs:
    day = "2026-03-27"
    user = {"location_label": "Los Angeles, CA"}
    overlays_enabled = {"neon_genie": True}
    tier_ctx = {"tier": "psychonaut"}


def test_stub_oracle_engine_blocked_without_explicit_gate(monkeypatch) -> None:
    monkeypatch.delenv("ABRAXAS_ALLOW_STUB_ORACLE", raising=False)
    monkeypatch.delenv("ABRAXAS_STUB_ORACLE_SCOPE", raising=False)
    uc = UserConfig.default()
    oc = OverlaysConfig.default()

    with pytest.raises(RuntimeError, match="ABRAXAS_ALLOW_STUB_ORACLE=1"):
        run_oracle_engine(uc, oc, "2026-03-27")

    with pytest.raises(RuntimeError, match="ABRAXAS_ALLOW_STUB_ORACLE=1"):
        _stub_engine_adapter(_Inputs())


def test_stub_oracle_engine_allowed_with_explicit_gate(monkeypatch) -> None:
    monkeypatch.setenv("ABRAXAS_ALLOW_STUB_ORACLE", "1")
    monkeypatch.setenv("ABRAXAS_STUB_ORACLE_SCOPE", "test")
    uc = UserConfig.default()
    oc = OverlaysConfig.default()

    readout, provenance = run_oracle_engine(uc, oc, "2026-03-27")
    assert readout["header"]["headline"] == "Interface spine online."
    assert provenance["engine"] == "stub_oracle_engine"

    payload = _stub_engine_adapter(_Inputs())
    assert payload["header"]["headline"].startswith("Stub engine adapter")


def test_stub_oracle_engine_blocked_when_scope_missing(monkeypatch) -> None:
    monkeypatch.setenv("ABRAXAS_ALLOW_STUB_ORACLE", "1")
    monkeypatch.delenv("ABRAXAS_STUB_ORACLE_SCOPE", raising=False)
    uc = UserConfig.default()
    oc = OverlaysConfig.default()

    with pytest.raises(RuntimeError, match=r"ABRAXAS_STUB_ORACLE_SCOPE=(dev\|test|test\|dev)"):
        run_oracle_engine(uc, oc, "2026-03-27")


def test_stub_oracle_engine_scope_required_even_if_pytest_env_present(monkeypatch) -> None:
    monkeypatch.setenv("ABRAXAS_ALLOW_STUB_ORACLE", "1")
    monkeypatch.delenv("ABRAXAS_STUB_ORACLE_SCOPE", raising=False)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "synthetic::nodeid")
    uc = UserConfig.default()
    oc = OverlaysConfig.default()

    with pytest.raises(RuntimeError, match=r"ABRAXAS_STUB_ORACLE_SCOPE=(dev\|test|test\|dev)"):
        run_oracle_engine(uc, oc, "2026-03-27")


def test_stub_oracle_engine_reports_invalid_scope(monkeypatch) -> None:
    monkeypatch.setenv("ABRAXAS_ALLOW_STUB_ORACLE", "1")
    monkeypatch.setenv("ABRAXAS_STUB_ORACLE_SCOPE", "prod")
    uc = UserConfig.default()
    oc = OverlaysConfig.default()

    with pytest.raises(RuntimeError, match="current scope: prod"):
        run_oracle_engine(uc, oc, "2026-03-27")


def test_stub_oracle_engine_allowed_for_dev_scope(monkeypatch) -> None:
    monkeypatch.setenv("ABRAXAS_ALLOW_STUB_ORACLE", "1")
    monkeypatch.setenv("ABRAXAS_STUB_ORACLE_SCOPE", "dev")
    uc = UserConfig.default()
    oc = OverlaysConfig.default()

    readout, _ = run_oracle_engine(uc, oc, "2026-03-27")
    assert readout["header"]["headline"] == "Interface spine online."
