"""Tests for real Chronos evidence provider (composes in-tree runes per SPEC)."""
from __future__ import annotations


def test_chronos_provider_emits_temporal_reasoning_and_has_confidence():
    """Provider with 4 regular-cadence events must emit TEMPORAL_REASONING with confidence > 0."""
    from abraxas.evidence.providers.chronos import create_chronos_adapter

    p = create_chronos_adapter()
    events = [
        {"timestamp": "2026-01-01T10:00:00Z", "source": "test"},
        {"timestamp": "2026-01-01T10:05:00Z", "source": "test"},
        {"timestamp": "2026-01-01T10:10:00Z", "source": "test"},
        {"timestamp": "2026-01-01T10:15:00Z", "source": "test"},
    ]
    env = p.produce_evidence("req-1", "test temporal reasoning claim", {"events": events})
    assert env.engine == "chronos"
    assert env.engine_version == "chronos.temporal.v1"
    assert env.model_identity == "chronos-rune-composer"
    assert env.evidence_type.value == "TEMPORAL_REASONING"
    assert env.confidence > 0.0
    assert env.provenance["rune_chain"] == ["scan", "align", "overlay", "packet"]
    assert env.provenance["lane"] == "SHADOW"


def test_chronos_provider_no_events_not_computable():
    """Provider must return not_computable provenance when context has no events."""
    from abraxas.evidence.providers.chronos import create_chronos_adapter

    p = create_chronos_adapter()
    env = p.produce_evidence("req-1", "test claim", {})
    assert env.engine == "chronos"
    assert env.confidence == 0.0
    assert env.uncertainty == 1.0
    assert env.provenance.get("not_computable") == "no_events"


def test_chronos_provider_empty_events_list_not_computable():
    """Provider handles empty events list — scan returns not_computable."""
    from abraxas.evidence.providers.chronos import create_chronos_adapter

    p = create_chronos_adapter()
    env = p.produce_evidence("req-1", "test claim", {"events": []})
    assert env.engine == "chronos"
    assert env.provenance.get("not_computable") is True


def test_chronos_provider_insufficient_events_not_computable():
    """Provider returns not_computable when fewer than 3 events (minimum for cadence)."""
    from abraxas.evidence.providers.chronos import create_chronos_adapter

    p = create_chronos_adapter()
    events = [
        {"timestamp": "2026-01-01T10:00:00Z"},
        {"timestamp": "2026-01-01T10:05:00Z"},
    ]
    env = p.produce_evidence("req-1", "test claim", {"events": events})
    assert env.engine == "chronos"
    assert env.provenance.get("not_computable") is True


def test_chronos_provider_provenance_has_rune_ids():
    """Provenance must include rune chain, lane, scan/align/overlay flags."""
    from abraxas.evidence.providers.chronos import create_chronos_adapter

    p = create_chronos_adapter()
    events = [
        {"timestamp": "2026-01-01T10:00:00Z"},
        {"timestamp": "2026-01-01T10:05:00Z"},
        {"timestamp": "2026-01-01T10:10:00Z"},
        {"timestamp": "2026-01-01T10:15:00Z"},
    ]
    env = p.produce_evidence("req-1", "test claim", {"events": events})
    provenance = env.provenance
    assert provenance["lane"] == "SHADOW"
    assert provenance["rune_chain"] == ["scan", "align", "overlay", "packet"]
    assert "scan_flags" in provenance
    assert "align_flags" in provenance
    assert "overlay_flags" in provenance
    assert "packet_status" in provenance
    # Regular cadence events should produce an active packet
    assert provenance["packet_status"] == "active"


def test_chronos_provider_with_symbolic_inputs():
    """Provider handles symbolic_inputs through the overlay rune."""
    from abraxas.evidence.providers.chronos import create_chronos_adapter

    p = create_chronos_adapter()
    events = [
        {"timestamp": "2026-01-01T10:00:00Z"},
        {"timestamp": "2026-01-01T10:05:00Z"},
        {"timestamp": "2026-01-01T10:10:00Z"},
        {"timestamp": "2026-01-01T10:15:00Z"},
    ]
    env = p.produce_evidence(
        "req-1",
        "test claim",
        {
            "events": events,
            "symbolic_inputs": ["new_moon", "marker:trade_opening"],
        },
    )
    assert env.engine == "chronos"
    # overlay_flags should be empty when valid symbolic inputs exist
    assert env.provenance["overlay_flags"] == []


def test_chronos_provider_exception_handling():
    """Provider must catch exceptions and return clean not_computable envelope."""
    from abraxas.evidence.providers.chronos import create_chronos_adapter

    p = create_chronos_adapter()
    # Passing non-list events should not crash but produce a rune error or be caught
    env = p.produce_evidence("req-1", "test claim", {"events": 42})
    assert env.engine == "chronos"
    # Either error in provenance or confidence == 0.0
    assert "error" in env.provenance or env.confidence == 0.0


def test_chronos_provider_window_config():
    """Provider passes window_config through to chrono_scan."""
    from abraxas.evidence.providers.chronos import create_chronos_adapter

    p = create_chronos_adapter()
    events = [
        {"timestamp": "2026-01-01T10:00:00Z"},
        {"timestamp": "2026-01-01T10:05:00Z"},
        {"timestamp": "2026-01-01T10:10:00Z"},
        {"timestamp": "2026-01-01T10:15:00Z"},
    ]
    env = p.produce_evidence(
        "req-1",
        "test claim",
        {
            "events": events,
            "window_config": {"lookback_span": "1h", "bucket_size": "10m"},
        },
    )
    assert env.engine == "chronos"


def test_chronos_provider_candidate_output_has_answer():
    """Candidate output must contain a meaningful answer string."""
    from abraxas.evidence.providers.chronos import create_chronos_adapter

    p = create_chronos_adapter()
    events = [
        {"timestamp": "2026-01-01T10:00:00Z"},
        {"timestamp": "2026-01-01T10:05:00Z"},
        {"timestamp": "2026-01-01T10:10:00Z"},
        {"timestamp": "2026-01-01T10:15:00Z"},
    ]
    env = p.produce_evidence("req-1", "test claim", {"events": events})
    assert len(env.candidate_outputs) > 0
    output = env.candidate_outputs[0]
    assert "packet_status" in output.answer
    assert "rune chain" in output.reasoning_trace.lower()


def test_chronos_provider_no_events_empty_candidates():
    """No events should yield empty candidate outputs."""
    from abraxas.evidence.providers.chronos import create_chronos_adapter

    p = create_chronos_adapter()
    env = p.produce_evidence("req-1", "test claim", {})
    assert len(env.candidate_outputs) == 0
