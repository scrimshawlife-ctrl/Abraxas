from __future__ import annotations

from abraxas.oracle.v2.wire import build_v2_block
from abraxas.oracle.v2.validate import validate_v2_block


def test_config_fingerprint_embedded_in_provenance_when_payload_provided():
    """Test that config fingerprint is embedded in provenance when config_payload is provided."""
    cfg = {
        "profile": "default",
        "thresholds": {"BW_HIGH": 20.0, "MRS_HIGH": 70.0},
        "features": {"ledger_enabled": True, "evidence_budget_bytes": 2000000},
    }
    v2 = build_v2_block(
        checks={
            "v1_golden_pass_rate": 1.0,
            "drift_budget_violations": 0,
            "evidence_bundle_overflow_rate": 0.0,
            "ci_volatility_correlation": 0.8,
            "interaction_noise_rate": 0.1,
        },
        router_input={
            "max_band_width": 1.0,
            "max_MRS": 1.0,
            "negative_signal_alerts": 0,
            "thresholds": {"BW_HIGH": 20.0, "MRS_HIGH": 70.0},
        },
        config_hash="FIXED_CONFIG_HASH_0000000000000000",
        config_payload=cfg,
        config_source="var/config/oracle_v2_config.json",
    )
    validate_v2_block(v2)
    mdp = v2["mode_decision"]["provenance"]
    cp = v2["compliance"]["provenance"]
    assert "config_fingerprint" in mdp
    assert "config_fingerprint" in cp
    assert mdp["config_fingerprint"] == cp["config_fingerprint"]
    assert mdp["config_source"] == "var/config/oracle_v2_config.json"
    assert cp["config_source"] == "var/config/oracle_v2_config.json"


def test_config_provenance_omitted_when_no_payload():
    """Test that config fingerprint and source are omitted when not provided."""
    v2 = build_v2_block(
        checks={
            "v1_golden_pass_rate": 1.0,
            "drift_budget_violations": 0,
            "evidence_bundle_overflow_rate": 0.0,
            "ci_volatility_correlation": 0.8,
            "interaction_noise_rate": 0.1,
        },
        router_input={
            "max_band_width": 1.0,
            "max_MRS": 1.0,
            "negative_signal_alerts": 0,
            "thresholds": {"BW_HIGH": 20.0, "MRS_HIGH": 70.0},
        },
        config_hash="FIXED_CONFIG_HASH_0000000000000000",
    )
    validate_v2_block(v2)
    mdp = v2["mode_decision"]["provenance"]
    cp = v2["compliance"]["provenance"]
    # Should only have config_hash
    assert "config_hash" in mdp
    assert "config_hash" in cp
    # Should not have fingerprint or source
    assert "config_fingerprint" not in mdp
    assert "config_source" not in mdp
    assert "config_fingerprint" not in cp
    assert "config_source" not in cp
