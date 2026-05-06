"""Tests for AAL-Viz projection extension with execution_summary."""
from __future__ import annotations
import pytest
from core.viz.projection import (
    build_execution_summary,
    extend_projection_packet,
    build_standalone_projection_packet,
)


def _make_run(status="completed", recommended="proceed"):
    return {
        "schema_version": "ShadowExecutionRun.v1",
        "run_id": "run-001",
        "status": status,
        "recommended_next_state": recommended,
    }


def _make_replay(deterministic_match=True, mismatched=None):
    return {
        "schema_version": "RuneReplayPacket.v1",
        "replay_id": "rep-001",
        "deterministic_match": deterministic_match,
        "mismatched_receipts": mismatched or [],
    }


def test_execution_summary_projection_only():
    summary = build_execution_summary([_make_run()], [_make_replay()])
    assert summary["projection_only"] is True


def test_execution_summary_no_inference_authority():
    summary = build_execution_summary([_make_run()], [_make_replay()])
    assert summary["inference_authority"] is False


def test_execution_summary_counts():
    runs = [_make_run(), _make_run()]
    replays = [_make_replay(True), _make_replay(False)]
    summary = build_execution_summary(runs, replays)
    assert summary["execution_runs"] == 2
    assert summary["replay_runs"] == 2
    assert summary["deterministic_matches"] == 1
    assert summary["failed_replays"] == 1


def test_execution_summary_rollback_ready():
    runs = [_make_run("completed", "proceed"), _make_run("failed", "rollback")]
    summary = build_execution_summary(runs, [])
    assert summary["rollback_ready"] == 1


def test_extend_projection_packet_adds_summary():
    base = {"schema_version": "AALVizProjectionPacket.v1", "pipeline_id": "p"}
    extended = extend_projection_packet(base, [_make_run()], [_make_replay()])
    assert "execution_summary" in extended
    assert extended["execution_summary"]["projection_only"] is True


def test_extend_projection_packet_updates_hash():
    base = {"schema_version": "AALVizProjectionPacket.v1", "pipeline_id": "p"}
    extended = extend_projection_packet(base, [_make_run()], [_make_replay()])
    assert "packet_hash" in extended
    assert len(extended["packet_hash"]) == 64


def test_extend_projection_does_not_mutate_base():
    base = {"schema_version": "AALVizProjectionPacket.v1", "pipeline_id": "p"}
    orig_keys = set(base.keys())
    extend_projection_packet(base, [_make_run()], [_make_replay()])
    assert set(base.keys()) == orig_keys


def test_standalone_projection_packet_shape():
    packet = build_standalone_projection_packet("pipe-001", [_make_run()], [_make_replay()])
    assert packet["schema_version"] == "AALVizProjectionPacket.v1"
    assert packet["projection_only"] is True
    assert packet["inference_authority"] is False
    assert "execution_summary" in packet
    assert "packet_hash" in packet


def test_standalone_packet_hash_deterministic():
    p1 = build_standalone_projection_packet("pipe-001", [_make_run()], [_make_replay(True)])
    p2 = build_standalone_projection_packet("pipe-001", [_make_run()], [_make_replay(True)])
    # Hashes should match for identical inputs
    assert p1["execution_summary"]["execution_runs"] == p2["execution_summary"]["execution_runs"]
    assert p1["execution_summary"]["deterministic_matches"] == p2["execution_summary"]["deterministic_matches"]


def test_empty_runs_and_replays():
    summary = build_execution_summary([], [])
    assert summary["execution_runs"] == 0
    assert summary["replay_runs"] == 0
    assert summary["deterministic_matches"] == 0
    assert summary["failed_replays"] == 0
    assert summary["rollback_ready"] == 0
