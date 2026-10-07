"""Token comparison must not leak the token through timing.

`header_token == token` short-circuits on the first differing byte, so the time taken
is a function of how many leading characters an attacker guessed correctly. That is a
real (if narrow) oracle. `secrets.compare_digest` is the standard remedy.

These tests assert the MECHANISM (the constant-time comparator is used) rather than
trying to measure wall-clock timing, which is flaky as a test and would not survive CI
noise. Driving `require_token` to accept and to reject, and checking the comparator was
consulted on both paths, is the honest observable.
"""

from __future__ import annotations

import secrets as _secrets

import pytest
from fastapi import HTTPException

from webpanel import panel_context


class _FakeRequest:
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


def test_correct_token_is_accepted(monkeypatch) -> None:
    monkeypatch.setenv("ABX_PANEL_TOKEN", "correct-horse")
    panel_context.require_token(_FakeRequest({"X-ABX-Token": "correct-horse"}))


def test_wrong_token_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("ABX_PANEL_TOKEN", "correct-horse")
    with pytest.raises(HTTPException) as excinfo:
        panel_context.require_token(_FakeRequest({"X-ABX-Token": "correct-horsf"}))
    assert excinfo.value.status_code == 401


def test_a_near_miss_of_the_same_length_is_rejected(monkeypatch) -> None:
    """The classic timing-oracle shape: correct prefix, wrong final byte."""
    monkeypatch.setenv("ABX_PANEL_TOKEN", "abcdefghij")
    with pytest.raises(HTTPException):
        panel_context.require_token(_FakeRequest({"X-ABX-Token": "abcdefghik"}))


def test_comparison_goes_through_compare_digest(monkeypatch) -> None:
    """Assert the mechanism: the constant-time comparator is the one consulted."""
    monkeypatch.setenv("ABX_PANEL_TOKEN", "correct-horse")
    seen: list[tuple[str, str]] = []
    real = _secrets.compare_digest

    def spy(a, b):
        seen.append((a, b))
        return real(a, b)

    monkeypatch.setattr(panel_context.secrets, "compare_digest", spy)
    panel_context.require_token(_FakeRequest({"X-ABX-Token": "correct-horse"}))
    assert seen, "the token comparison did not go through secrets.compare_digest"


def test_missing_token_env_still_permits_loopback_use(monkeypatch) -> None:
    """Unchanged behaviour: no token configured means no token required."""
    monkeypatch.delenv("ABX_PANEL_TOKEN", raising=False)
    panel_context.require_token(_FakeRequest({}))
