"""B: the Timechain check must distinguish 'not configured' from 'configured but unreachable'.

Written first (red), per the repo's TDD convention.

The defect this pins: `_check_timechain_connection()` returned False unconditionally, so
`get_status()` reported `timechain_available: False, fallback_mode: True` identically for
two operationally different situations:

  * Timechain was never configured  -> fallback is correct, expected, unremarkable
  * Timechain IS configured but the endpoint is down -> fallback is active because
    something is broken, and an operator needs to know

A status surface that answers the same in both cases is not a status surface. Same shape
as the audit's other findings: a component whose failure state is indistinguishable from
its success state.
"""
from __future__ import annotations

import pytest

from abraxas.yggdrasil.timechain import CypherTempreTimechain, TimechainConfig, TimechainState


class TestConnectionStateIsDistinguishable:
    def test_disabled_config_reports_not_configured(self):
        tc = CypherTempreTimechain(TimechainConfig(enabled=False))
        assert tc.connection_state() is TimechainState.NOT_CONFIGURED

    def test_enabled_but_unreachable_reports_unreachable(self):
        # 127.0.0.1:1 is reserved/unbound -> nothing can be listening there.
        cfg = TimechainConfig(enabled=True, endpoint="http://127.0.0.1:1", timeout=0.25, max_retries=1)
        tc = CypherTempreTimechain(cfg)
        assert tc.connection_state() is TimechainState.UNREACHABLE

    def test_the_two_states_are_NOT_equal(self):
        """The counterfactual: if these collapse, the whole fix is cosmetic."""
        disabled = CypherTempreTimechain(TimechainConfig(enabled=False)).connection_state()
        unreachable = CypherTempreTimechain(
            TimechainConfig(enabled=True, endpoint="http://127.0.0.1:1", timeout=0.25, max_retries=1)
        ).connection_state()
        assert disabled is not unreachable


class TestStatusSurface:
    def test_status_reports_not_configured_for_disabled(self):
        tc = CypherTempreTimechain(TimechainConfig(enabled=False))
        st = tc.get_status()
        assert st["timechain_state"] == TimechainState.NOT_CONFIGURED.value
        assert st["timechain_available"] is False
        assert st["fallback_mode"] is True

    def test_status_reports_unreachable_distinctly(self):
        cfg = TimechainConfig(enabled=True, endpoint="http://127.0.0.1:1", timeout=0.25, max_retries=1)
        st = CypherTempreTimechain(cfg).get_status()
        assert st["timechain_state"] == TimechainState.UNREACHABLE.value
        # still falling back -- but now the reason is explicit, not inferred
        assert st["fallback_mode"] is True

    def test_status_does_not_probe_twice(self):
        """get_status() called the check twice; a probe per call is a network round trip per call."""
        calls = {"n": 0}
        tc = CypherTempreTimechain(TimechainConfig(enabled=True, endpoint="http://127.0.0.1:1",
                                                   timeout=0.25, max_retries=1))
        original = tc._probe_endpoint
        def counted(*a, **k):
            calls["n"] += 1
            return original(*a, **k)
        tc._probe_endpoint = counted
        tc.get_status()
        assert calls["n"] <= 1, f"probed {calls['n']} times in one get_status()"


class TestFallbackStillWorks:
    def test_store_persists_when_unreachable(self, tmp_path):
        cfg = TimechainConfig(enabled=True, endpoint="http://127.0.0.1:1", timeout=0.25,
                              max_retries=1, fallback_to_file=True, file_storage_path=str(tmp_path))
        tc = CypherTempreTimechain(cfg)
        block_id, _ = tc.store({"k": "v"})
        assert block_id, "store() must still succeed via the file fallback"
        assert (tmp_path / "blocks.json").exists() or len(tc._blocks) > 0
