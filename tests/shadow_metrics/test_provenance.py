"""Tests for Shadow Structural Metrics provenance tracking.

Verifies that all metrics include complete provenance metadata.
"""

import pytest

from abraxas.runes.operators.sso import apply_sso


def test_provenance_completeness():
    """Verify all provenance fields are present."""
    context = {
        "symbol_pool": [{"sentiment": "positive"}],
        "metrics_requested": ["SEI"],
    }

    result = apply_sso(context)
    provenance = result["ssm_bundle"]["metrics"]["SEI"]["provenance"]

    # Required fields
    assert "run_id" in provenance
    assert "metric" in provenance
    assert "started_at_utc" in provenance
    assert "inputs_hash" in provenance
    assert "config_hash" in provenance
    assert "host" in provenance
    assert "seed_compliant" in provenance
    assert "no_influence_guarantee" in provenance

    # SEED compliance
    assert provenance["seed_compliant"] is True
    assert provenance["no_influence_guarantee"] is True


def test_all_metrics_have_provenance():
    """Verify all six metrics include provenance."""
    context = {
        "symbol_pool": [
            {
                "sentiment": "positive",
                "text": "Test",
                "narrative_id": "N1",
                "opinion_score": 0.5,
                "exposed_count": 10,
                "source": "A",
            }
        ],
    }

    result = apply_sso(context)

    for metric_id in ["SEI", "CLIP", "NOR", "PTS", "SCG", "FVC"]:
        metric_result = result["ssm_bundle"]["metrics"][metric_id]

        assert "provenance" in metric_result
        assert metric_result["provenance"]["metric"] == metric_id
        assert metric_result["provenance"]["seed_compliant"] is True


def test_isolation_proof_present():
    """Verify isolation proof is included in bundle."""
    context = {"symbol_pool": [{"sentiment": "neutral"}]}

    result = apply_sso(context)

    assert "isolation_proof" in result
    assert result["isolation_proof"].startswith("sha256:")


def test_bundle_hash_present():
    """Verify bundle hash is included."""
    context = {"symbol_pool": [{"sentiment": "neutral"}]}

    result = apply_sso(context)

    assert "bundle_hash" in result["ssm_bundle"]
    assert result["ssm_bundle"]["bundle_hash"].startswith("sha256:")


def test_audit_log_present():
    """Verify audit log is included in result."""
    context = {"symbol_pool": [{"sentiment": "neutral"}]}

    result = apply_sso(context)

    assert "audit_log" in result
    audit = result["audit_log"]

    assert audit["rune"] == "ϟ₇"
    assert audit["rune_name"] == "Shadow Structural Observer"
    assert audit["isolation_verified"] is True
    assert "metrics_computed" in audit
