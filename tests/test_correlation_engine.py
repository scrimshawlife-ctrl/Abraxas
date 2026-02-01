"""Tests for Correlation Engine v1."""

import pytest

from abraxas.correlation import CorrelationConfig, CorrelationEngine, CorrelationEvent


def test_correlation_engine_deterministic():
    """Test that correlation engine produces deterministic results."""
    config = CorrelationConfig(pair_rules=(("slang", "crypto"),), max_pairs=10)
    engine = CorrelationEngine()

    events_a = [
        CorrelationEvent("slang", "diamond_hands", 1.5, "2025-12-20T12:00:00Z"),
        CorrelationEvent("slang", "hodl", 2.0, "2025-12-20T13:00:00Z"),
    ]
    events_b = [
        CorrelationEvent("crypto", "diamond_hands", 1.2, "2025-12-20T12:30:00Z"),
        CorrelationEvent("crypto", "hodl", 1.8, "2025-12-20T13:30:00Z"),
    ]

    result1 = engine.run(
        events_a, events_b, domain_a="slang", domain_b="crypto", config=config, run_id="RUN-1"
    )
    result2 = engine.run(
        events_a, events_b, domain_a="slang", domain_b="crypto", config=config, run_id="RUN-1"
    )

    assert result1.deltas == result2.deltas
    assert result1.provenance.inputs_hash == result2.provenance.inputs_hash


def test_correlation_engine_shared_keys():
    """Test that only shared keys produce deltas."""
    config = CorrelationConfig(pair_rules=(("domain_a", "domain_b"),), max_pairs=10)
    engine = CorrelationEngine()

    events_a = [
        CorrelationEvent("domain_a", "shared", 1.0, "2025-12-20T12:00:00Z"),
        CorrelationEvent("domain_a", "only_a", 2.0, "2025-12-20T12:00:00Z"),
    ]
    events_b = [
        CorrelationEvent("domain_b", "shared", 1.5, "2025-12-20T12:00:00Z"),
        CorrelationEvent("domain_b", "only_b", 2.5, "2025-12-20T12:00:00Z"),
    ]

    result = engine.run(
        events_a, events_b, domain_a="domain_a", domain_b="domain_b", config=config, run_id="RUN-1"
    )

    assert len(result.deltas) == 1
    assert result.deltas[0].key == "shared"


def test_correlation_engine_latest_values():
    """Test that engine uses latest values for each key."""
    config = CorrelationConfig(pair_rules=(("a", "b"),), max_pairs=10)
    engine = CorrelationEngine()

    events_a = [
        CorrelationEvent("a", "key1", 1.0, "2025-12-20T12:00:00Z"),
        CorrelationEvent("a", "key1", 2.0, "2025-12-20T13:00:00Z"),  # Latest
    ]
    events_b = [
        CorrelationEvent("b", "key1", 1.5, "2025-12-20T12:30:00Z"),
    ]

    result = engine.run(events_a, events_b, domain_a="a", domain_b="b", config=config, run_id="RUN-1")

    # Should use latest value (2.0) from events_a
    assert len(result.deltas) == 1
    # Delta should be based on min(2.0, 1.5) = 1.5, with same sign
    assert result.deltas[0].delta == 1.5


def test_correlation_engine_max_pairs():
    """Test that max_pairs limit is enforced."""
    config = CorrelationConfig(pair_rules=(("a", "b"),), max_pairs=2)
    engine = CorrelationEngine()

    events_a = [
        CorrelationEvent("a", "key1", 3.0, "2025-12-20T12:00:00Z"),
        CorrelationEvent("a", "key2", 2.0, "2025-12-20T12:00:00Z"),
        CorrelationEvent("a", "key3", 1.0, "2025-12-20T12:00:00Z"),
    ]
    events_b = [
        CorrelationEvent("b", "key1", 3.0, "2025-12-20T12:00:00Z"),
        CorrelationEvent("b", "key2", 2.0, "2025-12-20T12:00:00Z"),
        CorrelationEvent("b", "key3", 1.0, "2025-12-20T12:00:00Z"),
    ]

    result = engine.run(events_a, events_b, domain_a="a", domain_b="b", config=config, run_id="RUN-1")

    # Should only return top 2
    assert len(result.deltas) == 2
    # Should be sorted by absolute delta (descending)
    assert abs(result.deltas[0].delta) >= abs(result.deltas[1].delta)


def test_correlation_engine_pair_validation():
    """Test that disallowed domain pairs are rejected."""
    config = CorrelationConfig(pair_rules=(("allowed_a", "allowed_b"),), max_pairs=10)
    engine = CorrelationEngine()

    events_a = [CorrelationEvent("forbidden_a", "key", 1.0, "2025-12-20T12:00:00Z")]
    events_b = [CorrelationEvent("forbidden_b", "key", 1.0, "2025-12-20T12:00:00Z")]

    with pytest.raises(ValueError, match="domain pair not allowed"):
        engine.run(
            events_a,
            events_b,
            domain_a="forbidden_a",
            domain_b="forbidden_b",
            config=config,
            run_id="RUN-1",
        )


def test_correlation_engine_bidirectional_pairs():
    """Test that pair rules work in both directions."""
    config = CorrelationConfig(pair_rules=(("a", "b"),), max_pairs=10)
    engine = CorrelationEngine()

    events_a = [CorrelationEvent("a", "key", 1.0, "2025-12-20T12:00:00Z")]
    events_b = [CorrelationEvent("b", "key", 1.5, "2025-12-20T12:00:00Z")]

    # Should work in both directions
    result1 = engine.run(events_a, events_b, domain_a="a", domain_b="b", config=config, run_id="RUN-1")
    result2 = engine.run(events_b, events_a, domain_a="b", domain_b="a", config=config, run_id="RUN-2")

    assert len(result1.deltas) == 1
    assert len(result2.deltas) == 1


def test_correlation_engine_delta_proxy():
    """Test delta proxy calculation."""
    config = CorrelationConfig(pair_rules=(("a", "b"),), max_pairs=10)
    engine = CorrelationEngine()

    # Same sign, positive
    events_a = [CorrelationEvent("a", "key1", 2.0, "2025-12-20T12:00:00Z")]
    events_b = [CorrelationEvent("b", "key1", 3.0, "2025-12-20T12:00:00Z")]
    result = engine.run(events_a, events_b, domain_a="a", domain_b="b", config=config, run_id="RUN-1")
    assert result.deltas[0].delta == 2.0  # min(2.0, 3.0) * 1.0

    # Different sign
    events_a = [CorrelationEvent("a", "key2", 2.0, "2025-12-20T12:00:00Z")]
    events_b = [CorrelationEvent("b", "key2", -3.0, "2025-12-20T12:00:00Z")]
    result = engine.run(events_a, events_b, domain_a="a", domain_b="b", config=config, run_id="RUN-2")
    assert result.deltas[0].delta == -2.0  # min(2.0, 3.0) * -1.0


def test_correlation_engine_provenance():
    """Test that engine includes proper provenance."""
    config = CorrelationConfig(pair_rules=(("a", "b"),), max_pairs=10)
    engine = CorrelationEngine()

    events_a = [CorrelationEvent("a", "key", 1.0, "2025-12-20T12:00:00Z")]
    events_b = [CorrelationEvent("b", "key", 1.5, "2025-12-20T12:00:00Z")]

    result = engine.run(
        events_a,
        events_b,
        domain_a="a",
        domain_b="b",
        config=config,
        run_id="PROV-TEST",
        git_sha="abc123",
        host="test-host",
    )

    assert result.provenance.run_id == "PROV-TEST"
    assert result.provenance.git_sha == "abc123"
    assert result.provenance.host == "test-host"
    assert result.provenance.inputs_hash is not None
    assert result.provenance.config_hash is not None


def test_correlation_engine_empty_events():
    """Test engine with no shared keys."""
    config = CorrelationConfig(pair_rules=(("a", "b"),), max_pairs=10)
    engine = CorrelationEngine()

    events_a = [CorrelationEvent("a", "key_a", 1.0, "2025-12-20T12:00:00Z")]
    events_b = [CorrelationEvent("b", "key_b", 1.5, "2025-12-20T12:00:00Z")]

    result = engine.run(events_a, events_b, domain_a="a", domain_b="b", config=config, run_id="RUN-1")

    assert len(result.deltas) == 0


def test_correlation_engine_sorting():
    """Test that deltas are sorted by absolute value descending."""
    config = CorrelationConfig(pair_rules=(("a", "b"),), max_pairs=10)
    engine = CorrelationEngine()

    events_a = [
        CorrelationEvent("a", "low", 1.0, "2025-12-20T12:00:00Z"),
        CorrelationEvent("a", "high", 5.0, "2025-12-20T12:00:00Z"),
        CorrelationEvent("a", "medium", 3.0, "2025-12-20T12:00:00Z"),
    ]
    events_b = [
        CorrelationEvent("b", "low", 1.0, "2025-12-20T12:00:00Z"),
        CorrelationEvent("b", "high", 5.0, "2025-12-20T12:00:00Z"),
        CorrelationEvent("b", "medium", 3.0, "2025-12-20T12:00:00Z"),
    ]

    result = engine.run(events_a, events_b, domain_a="a", domain_b="b", config=config, run_id="RUN-1")

    # Should be sorted by absolute delta descending
    assert result.deltas[0].key == "high"
    assert result.deltas[1].key == "medium"
    assert result.deltas[2].key == "low"
