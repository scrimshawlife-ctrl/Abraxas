"""Tests for runtime/concurrency module."""

import pytest

from abraxas.runtime.concurrency import ConcurrencyConfig


def test_default_config():
    """Verify default ConcurrencyConfig values."""
    cfg = ConcurrencyConfig()

    assert cfg.enabled is False
    assert cfg.max_workers_fetch == 4
    assert cfg.max_workers_parse == 4
    assert cfg.deterministic_commit is True


def test_workers_disabled():
    """When disabled, always returns 1 worker."""
    cfg = ConcurrencyConfig(enabled=False, max_workers_fetch=8, max_workers_parse=8)

    assert cfg.workers_for_stage("FETCH") == 1
    assert cfg.workers_for_stage("PARSE") == 1
    assert cfg.workers_for_stage("OTHER") == 1


def test_workers_enabled_fetch():
    """When enabled, FETCH stage uses max_workers_fetch."""
    cfg = ConcurrencyConfig(enabled=True, max_workers_fetch=6)

    assert cfg.workers_for_stage("FETCH") == 6


def test_workers_enabled_parse():
    """When enabled, PARSE stage uses max_workers_parse."""
    cfg = ConcurrencyConfig(enabled=True, max_workers_parse=3)

    assert cfg.workers_for_stage("PARSE") == 3


def test_workers_unknown_stage():
    """Unknown stages always return 1 worker."""
    cfg = ConcurrencyConfig(enabled=True, max_workers_fetch=8)

    assert cfg.workers_for_stage("UNKNOWN") == 1
    assert cfg.workers_for_stage("COMMIT") == 1


def test_config_is_frozen():
    """ConcurrencyConfig should be immutable."""
    cfg = ConcurrencyConfig()

    with pytest.raises(AttributeError):
        cfg.enabled = True
