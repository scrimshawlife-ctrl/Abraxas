"""Tests for RuneReplayPacket and replay_execution."""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.runes.replay import RuneReplayPacket
from core.execution.shadow_runner import run_shadow_execution
from core.execution.replay_runner import replay_execution

LOCKED_AUTHORITY = Authority(
    authority_id="auth.test.001",
    actor="test.actor",
    locked=True,
    scope="shadow_only",
)

RUNE_CATALOG = {
    "RUNE_AUDIT": {"input_schema": {}, "output_schema": {}},
}

ROUTE_GRAPH = {
    "graph_hash": "d" * 64,
    "RUNE_AUDIT": {"node": "node.audit", "edges": []},
}

CONTRACT = {
    "pipeline_id": "replay-test-001",
    "lane": "shadow",
    "required_runes": ["RUNE_AUDIT"],
    "authority": LOCKED_AUTHORITY,
    "metadata": {},
}


def test_replay_packet_creation():
    packet = RuneReplayPacket(
        replay_id="rep-001",
        source_execution_hash="a" * 64,
        replay_execution_hash="a" * 64,
        identical_output=True,
        deterministic_match=True,
        mismatched_receipts=[],
        authority=LOCKED_AUTHORITY,
        status="matched",
    )
    assert packet.schema_version == "RuneReplayPacket.v1"


def test_replay_packet_authority_locked():
    packet = RuneReplayPacket(
        replay_id="rep-001",
        source_execution_hash="a" * 64,
        replay_execution_hash="a" * 64,
        identical_output=True,
        deterministic_match=True,
        mismatched_receipts=[],
        authority=LOCKED_AUTHORITY,
        status="matched",
    )
    assert packet.authority.is_locked()


def test_replay_packet_mismatch_overrides_deterministic():
    packet = RuneReplayPacket(
        replay_id="rep-002",
        source_execution_hash="a" * 64,
        replay_execution_hash="b" * 64,
        identical_output=False,
        deterministic_match=False,
        mismatched_receipts=["rcpt-001"],
        authority=LOCKED_AUTHORITY,
        status="mismatch",
    )
    assert not packet.deterministic_match


def test_replay_execution_produces_packet():
    original = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    packet = replay_execution(original, CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert isinstance(packet, RuneReplayPacket)


def test_replay_execution_deterministic_match():
    """Same contract same graph => same hashes => deterministic match."""
    original = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    packet = replay_execution(original, CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert packet.deterministic_match is True


def test_replay_outputs_identical_hashes():
    """Replay of same contract produces identical receipt chain hash."""
    run1 = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    run2 = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    assert run1.receipt_chain_hash == run2.receipt_chain_hash
