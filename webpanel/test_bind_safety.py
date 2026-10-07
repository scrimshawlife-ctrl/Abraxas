"""The panel must not expose an unauthenticated console to the network.

Two behaviours, and the second is what keeps the first from being a broken default:

1. A non-loopback bind with no ABX_PANEL_TOKEN is REFUSED. Exposing the operator
   console on the LAN without a credential was possible before; the repo documented
   the ABX_PANEL_HOST=0.0.0.0 opt-in and warned about it, but a warning is not a
   control.
2. A loopback bind with no token still WORKS. This is the counterfactual: without it,
   a rule that refuses everything would satisfy test 1 while breaking every local
   user. The guard's narrowness has to be enforced, not intended.
"""

from __future__ import annotations

import pytest

from webpanel.panel_context import _is_loopback_host, ensure_bind_is_safe


# ── the refusal ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "host",
    ["0.0.0.0", "::", "192.168.1.10", "10.0.0.5", "example.internal"],
)
def test_non_loopback_bind_without_token_is_refused(host: str, monkeypatch) -> None:
    monkeypatch.delenv("ABX_PANEL_TOKEN", raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        ensure_bind_is_safe(host)
    message = str(excinfo.value)
    assert "ABX_PANEL_TOKEN" in message
    assert host in message


# ── the counterfactual: the default must keep working ────────────────────────

@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_loopback_bind_without_token_is_allowed(host: str, monkeypatch) -> None:
    monkeypatch.delenv("ABX_PANEL_TOKEN", raising=False)
    ensure_bind_is_safe(host)  # must not raise


def test_non_loopback_bind_with_token_is_allowed(monkeypatch) -> None:
    monkeypatch.setenv("ABX_PANEL_TOKEN", "a-real-token")
    ensure_bind_is_safe("0.0.0.0")  # must not raise


def test_empty_token_counts_as_no_token(monkeypatch) -> None:
    monkeypatch.setenv("ABX_PANEL_TOKEN", "   ")
    with pytest.raises(RuntimeError):
        ensure_bind_is_safe("0.0.0.0")


# ── the classifier itself ────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "host,expected",
    [
        ("127.0.0.1", True),
        ("localhost", True),
        ("::1", True),
        ("127.0.0.2", True),   # the whole 127.0.0.0/8 block is loopback
        ("0.0.0.0", False),
        ("::", False),
        ("192.168.0.1", False),
        ("8.8.8.8", False),
    ],
)
def test_is_loopback_host(host: str, expected: bool) -> None:
    assert _is_loopback_host(host) is expected
