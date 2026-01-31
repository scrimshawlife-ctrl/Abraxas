"""Tests for oracle API endpoints."""

from __future__ import annotations

from datetime import date

import pytest


def test_imports():
    """Test that all modules can be imported."""
    from abraxas.api.app import app
    from abraxas.api.routes import router
    from abraxas.api.ws import WebSocketPublisher
    from abraxas.api.ws_bridge import wire_bus_to_ws
    from abraxas.events.bus import EventBus
    from abraxas.oracle.cli import main
    from abraxas.oracle.runner import DeterministicOracleRunner, OracleConfig
    from abraxas.oracle.transforms import CorrelationDelta

    assert app is not None
    assert router is not None
    assert WebSocketPublisher is not None
    assert wire_bus_to_ws is not None
    assert EventBus is not None
    assert main is not None
    assert DeterministicOracleRunner is not None
    assert OracleConfig is not None
    assert CorrelationDelta is not None


def test_oracle_runner():
    """Test oracle runner with sample data."""
    from abraxas.oracle.runner import DeterministicOracleRunner, OracleConfig
    from abraxas.oracle.transforms import CorrelationDelta

    deltas = [
        CorrelationDelta(
            domain_a="crypto",
            domain_b="social",
            key="bitcoin",
            delta=0.85,
            observed_at_utc="2025-12-20T10:30:00Z",
        ),
        CorrelationDelta(
            domain_a="tech",
            domain_b="finance",
            key="ai",
            delta=0.91,
            observed_at_utc="2025-12-20T09:45:00Z",
        ),
    ]

    runner = DeterministicOracleRunner()
    cfg = OracleConfig(half_life_hours=24.0, top_k=5)
    art = runner.run_for_date(date(2025, 12, 20), deltas, cfg)

    assert art.id is not None
    assert art.date == "2025-12-20"
    assert art.signature is not None
    assert len(art.signature) == 64  # SHA256 hex
    assert art.output["top_k"] == 5
    assert len(art.output["signals"]) == 2  # Both deltas
    assert art.provenance.run_id == art.id


def test_event_bus():
    """Test event bus pub/sub."""
    from abraxas.events.bus import EventBus

    bus = EventBus()
    events_received = []

    def handler(payload):
        events_received.append(payload)

    bus.subscribe("test", handler)
    bus.publish("test", {"value": 42})

    assert len(events_received) == 1
    assert events_received[0]["value"] == 42


def test_lexicon_engine():
    """Test lexicon engine with in-memory registry."""
    from abraxas.lexicon.engine import InMemoryLexiconRegistry, LexiconEngine, LexiconEntry, LexiconPack

    reg = InMemoryLexiconRegistry()
    eng = LexiconEngine(reg)

    pack = LexiconPack(
        domain="crypto",
        version="1.0",
        entries=(
            LexiconEntry(token="bitcoin", weight=0.9, meta={}),
            LexiconEntry(token="ethereum", weight=0.85, meta={}),
        ),
        created_at_utc="2025-12-20T00:00:00Z",
    )

    eng.register(pack)
    resolved = eng.resolve("crypto", "1.0")
    assert resolved.domain == "crypto"
    assert resolved.version == "1.0"
    assert len(resolved.entries) == 2

    # Test compression
    result = eng.compress("crypto", ["bitcoin", "unknown", "ethereum"], run_id="test-123")
    assert len(result.matched) == 2
    assert len(result.unmatched) == 1
    assert "bitcoin" in result.weights_out
    assert "ethereum" in result.weights_out
    assert result.weights_out["bitcoin"] == 0.9
