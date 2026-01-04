"""Test shadow metrics access gate (ϟ₇ SSO rune requirement).

P0 security test: Shadow metrics can only be accessed via ϟ₇ SSO rune.
Direct access must be blocked by kernel.
"""

import pytest
from unittest.mock import patch, MagicMock


def test_shadow_lane_requires_sso_rune():
    """Shadow lane runes must require ϟ₇ authorization."""
    from abx.kernel import invoke

    # Mock registry with shadow lane rune
    shadow_rune = {
        "rune_id": "test.shadow.metric",
        "evidence_mode": "shadow_lane"
    }

    with patch("abx.kernel.load_registry") as mock_registry, \
         patch("abx.kernel.load_policy") as mock_policy, \
         patch("abx.kernel.is_allowed", return_value=True):

        mock_registry.return_value = {"runes": [shadow_rune]}
        mock_policy.return_value = {}

        # Attempt without ϟ₇ authorization - should fail
        with pytest.raises(PermissionError) as exc_info:
            invoke(
                rune_id="test.shadow.metric",
                payload={},
                context={}  # No authorized_runes
            )

        assert "ϟ₇" in str(exc_info.value)
        assert "Shadow Structural Observer" in str(exc_info.value)
        assert "Shadow lane access denied" in str(exc_info.value)


def test_shadow_lane_allowed_with_sso_rune():
    """Shadow lane access succeeds with ϟ₇ authorization."""
    from abx.kernel import invoke

    shadow_rune = {
        "rune_id": "test.shadow.metric",
        "evidence_mode": "shadow_lane"
    }

    def mock_shadow_operator(**kwargs):
        return {"shadow_metric": 0.5}

    with patch("abx.kernel.load_registry") as mock_registry, \
         patch("abx.kernel.load_policy") as mock_policy, \
         patch("abx.kernel.is_allowed", return_value=True), \
         patch("abx.kernel.payload_schema_for", return_value=None), \
         patch("abx.kernel.result_schema_for", return_value=None), \
         patch("abx.kernel.record_invocation"), \
         patch("abx.kernel.record_event"), \
         patch("abx.kernel.emit_event"):

        mock_registry.return_value = {"runes": [shadow_rune]}
        mock_policy.return_value = {}

        # Mock the operator dispatch
        with patch.dict("sys.modules", {"test.shadow": MagicMock()}):
            # This would need actual operator implementation
            # For now, test just verifies authorization check passes
            try:
                invoke(
                    rune_id="test.shadow.metric",
                    payload={},
                    context={"authorized_runes": ["ϟ₇"]}  # With ϟ₇ auth
                )
            except NotImplementedError:
                # Expected - operator not actually implemented
                # But authorization check passed (didn't raise PermissionError)
                pass


def test_prediction_lane_no_sso_required():
    """Prediction lane runes don't require ϟ₇ authorization."""
    from abx.kernel import invoke

    prediction_rune = {
        "rune_id": "test.prediction.metric",
        "evidence_mode": "prediction_lane"
    }

    def mock_prediction_operator(**kwargs):
        return {"prediction": 0.8}

    with patch("abx.kernel.load_registry") as mock_registry, \
         patch("abx.kernel.load_policy") as mock_policy, \
         patch("abx.kernel.is_allowed", return_value=True), \
         patch("abx.kernel.payload_schema_for", return_value=None), \
         patch("abx.kernel.result_schema_for", return_value=None), \
         patch("abx.kernel.record_invocation"), \
         patch("abx.kernel.record_event"), \
         patch("abx.kernel.emit_event"):

        mock_registry.return_value = {"runes": [prediction_rune]}
        mock_policy.return_value = {}

        # Prediction lane should work without ϟ₇
        try:
            invoke(
                rune_id="test.prediction.metric",
                payload={},
                context={}  # No authorization needed
            )
        except (NotImplementedError, KeyError):
            # Expected - operator dispatch not fully mocked
            # But authorization check passed
            pass
