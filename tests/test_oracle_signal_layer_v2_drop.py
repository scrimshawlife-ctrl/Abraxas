from __future__ import annotations

from abx.oracle_signal_layer_v2 import (
    NOT_COMPUTABLE,
    OracleSignalLayerError,
    build_validator_summary,
    run_invariance,
    run_oracle_signal_layer_v2,
)


def _envelope() -> dict:
    return {
        "schema_id": "OracleSignalInputEnvelope.v2",
        "run_id": "run_oracle_v2_001",
        "lane": "forecast-active",
        "observations": [
            {
                "observation_id": "obs_b",
                "domain": "market",
                "subdomain": "rates",
                "impact": 0.8,
                "velocity": 0.6,
                "uncertainty": 0.2,
                "polarity": 0.1,
                "tags": ["macro", "policy"],
            },
            {
                "observation_id": "obs_a",
                "domain": "market",
                "subdomain": "rates",
                "impact": 0.6,
                "velocity": 0.5,
                "uncertainty": 0.4,
                "polarity": 0.2,
                "tags": ["macro"],
            },
        ],
        "trend_inputs": [{"label": "rates_1w", "value": 0.11}],
        "provenance": {"source": "fixture"},
    }


def test_runtime_emits_authority_and_advisory_boundaries() -> None:
    out = run_oracle_signal_layer_v2(_envelope())
    assert out["schema_id"] == "OracleSignalLayerOutput.v2"
    assert out["authority_advisory_boundary_enforced"] is True
    assert out["authority"]["schema_id"] == "OracleSignalAuthorityOutput.v2"
    assert len(out["authority"]["signal_items"]) == 1
    assert len(out["advisory_attachments"]) == 2
    assert {x["attachment_id"] for x in out["advisory_attachments"]} == {"mircl", "trend"}


def test_invariance_digest_is_stable() -> None:
    report = run_invariance(_envelope(), repeats=5)
    assert report["status"] == "PASS"
    assert report["input_invariant"] is True
    assert report["output_invariant"] is True
    assert report["authority_invariant"] is True


def test_missing_trend_is_not_computable() -> None:
    env = _envelope()
    env["trend_inputs"] = []
    out = run_oracle_signal_layer_v2(env)
    trend = [x for x in out["advisory_attachments"] if x["attachment_id"] == "trend"][0]
    assert trend["status"] == NOT_COMPUTABLE
    summary = build_validator_summary(out)
    assert "trend" in summary["not_computable_attachments"]


def test_validator_summary_hashes_and_counts() -> None:
    out = run_oracle_signal_layer_v2(_envelope())
    summary = build_validator_summary(out)
    assert summary["schema_id"] == "OracleValidatorSummary.v1"
    assert summary["status"] == "PASS"
    assert summary["authority_item_count"] == 1
    assert summary["advisory_attachment_count"] == 2
    assert isinstance(summary["input_hash"], str) and summary["input_hash"]
    assert isinstance(summary["output_hash"], str) and summary["output_hash"]


def test_invalid_envelope_rejected() -> None:
    bad = _envelope()
    bad["schema_id"] = "wrong"
    try:
        run_oracle_signal_layer_v2(bad)
        assert False, "expected OracleSignalLayerError"
    except OracleSignalLayerError:
        assert True
