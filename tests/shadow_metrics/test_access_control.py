"""Tests for Shadow Structural Metrics access control.

Verifies that direct access is blocked and only ABX-Runes access is permitted.
"""

import pytest


def test_direct_import_blocked():
    """Verify that direct imports of Shadow Structural Metrics are blocked."""
    with pytest.raises(Exception) as exc_info:
        from abraxas.shadow_metrics import compute_sei  # noqa: F401

    assert "AccessDeniedError" in str(exc_info.typename)
    assert "ABX-Runes" in str(exc_info.value)


def test_direct_module_access_blocked():
    """Verify that direct module access is blocked."""
    with pytest.raises(Exception) as exc_info:
        from abraxas.shadow_metrics import core  # noqa: F401

    assert "AccessDeniedError" in str(exc_info.typename)


def test_metric_name_access_blocked():
    """Verify that accessing metric names directly is blocked."""
    with pytest.raises(Exception) as exc_info:
        from abraxas.shadow_metrics import SEI  # noqa: F401

    assert "AccessDeniedError" in str(exc_info.typename)


def test_version_access_allowed():
    """Verify that __version__ can be accessed."""
    from abraxas import shadow_metrics

    assert hasattr(shadow_metrics, "__version__")
    assert shadow_metrics.__version__ == "1.0.0"


def test_internal_rune_access_exists():
    """Verify that _internal_rune_access exists but is protected."""
    from abraxas import shadow_metrics

    assert hasattr(shadow_metrics, "_internal_rune_access")

    # Calling it directly should fail (not from rune operator)
    with pytest.raises(RuntimeError) as exc_info:
        shadow_metrics._internal_rune_access()

    assert "Unauthorized caller" in str(exc_info.value)
