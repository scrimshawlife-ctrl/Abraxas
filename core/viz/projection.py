"""AAL-Viz projection extension: execution summary.

Extends the AAL-Viz projection packet with rune-layer execution metrics.
Still:
  - projection_only = True
  - inference_authority = False
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, Dict, List
import json


def build_execution_summary(
    execution_runs: List[Dict[str, Any]],
    replay_packets: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build projection-only execution summary from run and replay data.

    Args:
        execution_runs: List of ShadowExecutionRun dicts.
        replay_packets: List of RuneReplayPacket dicts.

    Returns:
        execution_summary dict for embedding in AAL-Viz projection packet.

    Notes:
        projection_only = True
        inference_authority = False
        No Canon mutation.
        No forecast activation.
    """
    run_count = len(execution_runs)
    replay_count = len(replay_packets)

    deterministic_matches = sum(
        1 for p in replay_packets if p.get("deterministic_match", False)
    )
    failed_replays = replay_count - deterministic_matches

    rollback_ready_count = sum(
        1 for run in execution_runs
        if run.get("recommended_next_state") == "rollback"
        or run.get("status") in {"failed", "partial"}
    )

    return {
        "schema_version": "ExecutionSummary.v1",
        "projection_only": True,
        "inference_authority": False,
        "execution_runs": run_count,
        "replay_runs": replay_count,
        "deterministic_matches": deterministic_matches,
        "failed_replays": failed_replays,
        "rollback_ready": rollback_ready_count,
    }


def extend_projection_packet(
    base_packet: Dict[str, Any],
    execution_runs: List[Dict[str, Any]],
    replay_packets: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Extend an existing AAL-Viz projection packet with execution summary.

    Args:
        base_packet: Existing projection packet dict.
        execution_runs: List of ShadowExecutionRun dicts.
        replay_packets: List of RuneReplayPacket dicts.

    Returns:
        Extended projection packet. Immutable - creates a new dict.
    """
    extended = dict(base_packet)
    extended["execution_summary"] = build_execution_summary(
        execution_runs, replay_packets
    )

    # Recompute packet hash to include execution_summary
    canonical = json.dumps(extended, sort_keys=True).encode("utf-8")
    extended["packet_hash"] = sha256(canonical).hexdigest()

    return extended


def build_standalone_projection_packet(
    pipeline_id: str,
    execution_runs: List[Dict[str, Any]],
    replay_packets: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build a standalone projection packet with execution summary.

    Args:
        pipeline_id: The pipeline this packet covers.
        execution_runs: List of ShadowExecutionRun dicts.
        replay_packets: List of RuneReplayPacket dicts.

    Returns:
        Projection packet dict with execution_summary embedded.
    """
    summary = build_execution_summary(execution_runs, replay_packets)

    packet = {
        "schema_version": "AALVizProjectionPacket.v1",
        "pipeline_id": pipeline_id,
        "projection_only": True,
        "inference_authority": False,
        "execution_summary": summary,
    }

    canonical = json.dumps(packet, sort_keys=True).encode("utf-8")
    packet["packet_hash"] = sha256(canonical).hexdigest()

    return packet
