"""Tests for Oracle Pipeline v1 with golden signature tests."""

import pytest
from datetime import date

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.oracle.runner import DeterministicOracleRunner, OracleConfig
from abraxas.oracle.transforms import CorrelationDelta, decay, score_deltas


def test_oracle_signature_is_stable():
    """Golden test: Oracle signature must remain stable across runs."""
    runner = DeterministicOracleRunner(git_sha="deadbeef", host="test-host")
    cfg = OracleConfig(half_life_hours=24.0, top_k=2)

    deltas = [
        CorrelationDelta("slang", "crypto", "diamond_hands", 1.5, "2025-12-20T00:00:00Z"),
        CorrelationDelta("idiom", "tech", "move_fast", 0.7, "2025-12-19T12:00:00Z"),
    ]

    art = runner.run_for_date(
        date(2025, 12, 20), deltas, cfg, run_id="RUN-123", as_of_utc="2025-12-20T23:59:59Z"
    )

    # Golden signature: recompute exactly (artifact minus signature)
    artifact_wo_sig = {
        "id": art.id,
        "date": art.date,
        "inputs": art.inputs,
        "output": art.output,
        "provenance": art.provenance.__dict__,
    }
    expected = sha256_hex(canonical_json(artifact_wo_sig))
    assert art.signature == expected


def test_oracle_deterministic_output():
    """Test that oracle output is deterministic for same inputs."""
    runner = DeterministicOracleRunner(git_sha="abc123", host="test")
    cfg = OracleConfig(half_life_hours=24.0, top_k=3)

    deltas = [
        CorrelationDelta("domain1", "domain2", "key1", 1.0, "2025-12-20T12:00:00Z"),
        CorrelationDelta("domain1", "domain2", "key2", 2.0, "2025-12-20T10:00:00Z"),
    ]

    art1 = runner.run_for_date(
        date(2025, 12, 20), deltas, cfg, run_id="RUN-A", as_of_utc="2025-12-20T23:59:59Z"
    )
    art2 = runner.run_for_date(
        date(2025, 12, 20), deltas, cfg, run_id="RUN-A", as_of_utc="2025-12-20T23:59:59Z"
    )

    # Same inputs + run_id should produce same signature
    assert art1.signature == art2.signature
    assert art1.output == art2.output


def test_oracle_decay_weighting():
    """Test that decay weighting affects signal scores."""
    runner = DeterministicOracleRunner()
    cfg = OracleConfig(half_life_hours=24.0, top_k=10)

    # Recent signal vs old signal with same delta
    deltas = [
        CorrelationDelta("a", "b", "recent", 1.0, "2025-12-20T20:00:00Z"),
        CorrelationDelta("a", "b", "old", 1.0, "2025-12-19T20:00:00Z"),
    ]

    art = runner.run_for_date(date(2025, 12, 20), deltas, cfg, as_of_utc="2025-12-20T23:59:59Z")

    signals = art.output["signals"]
    assert len(signals) == 2

    # Recent signal should have higher score due to less decay
    recent = next(s for s in signals if s["key"] == "recent")
    old = next(s for s in signals if s["key"] == "old")

    assert recent["score"] > old["score"]
    assert recent["age_hours"] < old["age_hours"]


def test_oracle_top_k_limiting():
    """Test that oracle respects top_k limit."""
    runner = DeterministicOracleRunner()
    cfg = OracleConfig(half_life_hours=24.0, top_k=2)

    deltas = [
        CorrelationDelta("a", "b", "signal1", 3.0, "2025-12-20T12:00:00Z"),
        CorrelationDelta("a", "b", "signal2", 2.0, "2025-12-20T12:00:00Z"),
        CorrelationDelta("a", "b", "signal3", 1.0, "2025-12-20T12:00:00Z"),
    ]

    art = runner.run_for_date(date(2025, 12, 20), deltas, cfg, as_of_utc="2025-12-20T23:59:59Z")

    # Only top 2 signals in output
    assert len(art.output["signals"]) == 2
    assert art.output["top_k"] == 2

    # But aggregate should count all 3
    assert art.output["aggregate"]["count"] == 3


def test_oracle_signal_sorting():
    """Test that signals are sorted by score (descending)."""
    runner = DeterministicOracleRunner()
    cfg = OracleConfig(half_life_hours=24.0, top_k=10)

    deltas = [
        CorrelationDelta("a", "b", "low", 1.0, "2025-12-20T12:00:00Z"),
        CorrelationDelta("a", "b", "high", 5.0, "2025-12-20T12:00:00Z"),
        CorrelationDelta("a", "b", "medium", 3.0, "2025-12-20T12:00:00Z"),
    ]

    art = runner.run_for_date(date(2025, 12, 20), deltas, cfg, as_of_utc="2025-12-20T23:59:59Z")

    signals = art.output["signals"]
    scores = [s["score"] for s in signals]

    # Scores should be in descending order
    assert scores == sorted(scores, reverse=True)
    assert signals[0]["key"] == "high"
    assert signals[1]["key"] == "medium"
    assert signals[2]["key"] == "low"


def test_oracle_provenance_tracking():
    """Test that oracle includes proper provenance."""
    runner = DeterministicOracleRunner(git_sha="test-sha", host="test-host")
    cfg = OracleConfig(half_life_hours=12.0, top_k=5)

    deltas = [CorrelationDelta("a", "b", "key", 1.0, "2025-12-20T12:00:00Z")]

    art = runner.run_for_date(date(2025, 12, 20), deltas, cfg, run_id="PROV-TEST")

    assert art.provenance.run_id == "PROV-TEST"
    assert art.provenance.git_sha == "test-sha"
    assert art.provenance.host == "test-host"
    assert art.provenance.inputs_hash is not None
    assert art.provenance.config_hash is not None


def test_decay_function():
    """Test exponential decay function."""
    # At half-life, should be 0.5
    assert decay(24.0, 24.0) == 0.5

    # At 0 age, should be 1.0
    assert decay(0.0, 24.0) == 1.0

    # At 2x half-life, should be 0.25
    assert decay(48.0, 24.0) == 0.25

    # Should raise on invalid half-life
    with pytest.raises(ValueError):
        decay(10.0, 0.0)

    with pytest.raises(ValueError):
        decay(10.0, -1.0)


def test_score_deltas_deterministic():
    """Test that score_deltas produces deterministic results."""
    deltas = [
        CorrelationDelta("a", "b", "key1", 1.5, "2025-12-20T12:00:00Z"),
        CorrelationDelta("c", "d", "key2", 2.0, "2025-12-20T10:00:00Z"),
    ]

    result1 = score_deltas(deltas, as_of_utc="2025-12-20T23:59:59Z", half_life_hours=24.0)
    result2 = score_deltas(deltas, as_of_utc="2025-12-20T23:59:59Z", half_life_hours=24.0)

    assert result1 == result2


def test_score_deltas_sorting():
    """Test that score_deltas sorts by score, then pair, then key, then time."""
    deltas = [
        CorrelationDelta("b", "c", "z", 1.0, "2025-12-20T12:00:00Z"),
        CorrelationDelta("a", "b", "a", 2.0, "2025-12-20T12:00:00Z"),
        CorrelationDelta("a", "b", "z", 2.0, "2025-12-20T12:00:00Z"),
    ]

    result = score_deltas(deltas, as_of_utc="2025-12-20T23:59:59Z", half_life_hours=24.0)

    # First two have higher scores (delta=2.0)
    assert result[0]["delta"] == 2.0
    assert result[1]["delta"] == 2.0
    assert result[2]["delta"] == 1.0

    # Among same scores, sorted by pair then key
    assert result[0]["pair"] == "a~b"
    assert result[0]["key"] == "a"
    assert result[1]["pair"] == "a~b"
    assert result[1]["key"] == "z"


def test_oracle_empty_deltas():
    """Test oracle generation with no deltas."""
    runner = DeterministicOracleRunner()
    cfg = OracleConfig(half_life_hours=24.0, top_k=10)

    art = runner.run_for_date(date(2025, 12, 20), [], cfg)

    assert art.output["signals"] == []
    assert art.output["aggregate"]["count"] == 0
    assert art.output["aggregate"]["score_sum"] == 0.0
    assert art.signature is not None  # Should still have valid signature


def test_oracle_date_formatting():
    """Test that oracle date is properly formatted."""
    runner = DeterministicOracleRunner()
    cfg = OracleConfig(half_life_hours=24.0, top_k=5)

    art = runner.run_for_date(date(2025, 12, 20), [], cfg)

    assert art.date == "2025-12-20"


def test_oracle_inputs_captured():
    """Test that all inputs are captured in artifact."""
    runner = DeterministicOracleRunner()
    cfg = OracleConfig(half_life_hours=12.0, top_k=3)

    deltas = [CorrelationDelta("a", "b", "key", 1.0, "2025-12-20T12:00:00Z")]

    art = runner.run_for_date(date(2025, 12, 20), deltas, cfg, as_of_utc="2025-12-20T23:59:59Z")

    assert art.inputs["as_of_utc"] == "2025-12-20T23:59:59Z"
    assert art.inputs["config"]["half_life_hours"] == 12.0
    assert art.inputs["config"]["top_k"] == 3
    assert len(art.inputs["deltas"]) == 1
    assert art.inputs["deltas"][0]["domain_a"] == "a"
    assert art.inputs["deltas"][0]["key"] == "key"
