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
    uc = UserConfig.default()
    oc = OverlaysConfig.default()

    with pytest.raises(RuntimeError, match="ABRAXAS_ALLOW_STUB_ORACLE=1"):
        run_oracle_engine(uc, oc, "2026-03-27")

    with pytest.raises(RuntimeError, match="ABRAXAS_ALLOW_STUB_ORACLE=1"):
        _stub_engine_adapter(_Inputs())


def test_stub_oracle_engine_allowed_with_explicit_gate(monkeypatch) -> None:
    monkeypatch.setenv("ABRAXAS_ALLOW_STUB_ORACLE", "1")
    uc = UserConfig.default()
    oc = OverlaysConfig.default()

    readout, provenance = run_oracle_engine(uc, oc, "2026-03-27")
    assert readout["header"]["headline"] == "Interface spine online."
    assert provenance["engine"] == "stub_oracle_engine"

    payload = _stub_engine_adapter(_Inputs())
    assert payload["header"]["headline"].startswith("Stub engine adapter")
