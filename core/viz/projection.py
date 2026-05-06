"""AAL-Viz projection extension: execution summary + sandbox summary.

Extends the AAL-Viz projection packet with:
- rune-layer execution metrics (v2.0.1)
- adaptive sandbox metrics (v2.0.5)

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


# ── v2.0.5 Adaptive Sandbox projection extensions ─────────────────────────

def build_sandbox_summary(
    adaptive_branches: List[Dict[str, Any]],
    replay_packets: List[Dict[str, Any]],
    stabilization_packets: List[Dict[str, Any]],
    promotion_candidates: List[Dict[str, Any]],
    lineage_packets: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build projection-only sandbox summary for AAL-Viz.

    Args:
        adaptive_branches: List of AdaptiveSandboxBranch dicts.
        replay_packets: List of SandboxReplayPacket dicts.
        stabilization_packets: List of SandboxStabilizationPacket dicts.
        promotion_candidates: List of SandboxPromotionCandidate dicts.
        lineage_packets: List of AdaptiveBranchLineage dicts.

    Returns:
        sandbox_summary dict.

    Notes:
        projection_only = True
        inference_authority = False
        No Canon mutation.
        No forecast activation.
    """
    branch_count = len(adaptive_branches)

    replay_matches = sum(
        1 for p in replay_packets if p.get("deterministic_match", False)
    )

    unstable_count = sum(
        1 for b in adaptive_branches
        if b.get("stabilization_state") in {"unstable", "failed"}
    )

    promotion_candidate_count = len(promotion_candidates)
    blocked_promotions = sum(
        1 for c in promotion_candidates
        if c.get("promotion_allowed", False) is False
    )

    lineage_depth = max(
        (lp.get("lineage_depth", 0) for lp in lineage_packets), default=0
    )

    sandbox_failures = sum(
        1 for b in adaptive_branches if b.get("status") == "failed"
    )

    return {
        "schema_version": "SandboxSummary.v1",
        "projection_only": True,
        "inference_authority": False,
        "adaptive_branches": branch_count,
        "replay_matches": replay_matches,
        "unstable_branches": unstable_count,
        "promotion_candidates": promotion_candidate_count,
        "blocked_promotions": blocked_promotions,
        "lineage_depth": lineage_depth,
        "sandbox_failures": sandbox_failures,
    }


def extend_projection_packet_with_sandbox(
    base_packet: Dict[str, Any],
    adaptive_branches: List[Dict[str, Any]],
    replay_packets: List[Dict[str, Any]],
    stabilization_packets: List[Dict[str, Any]],
    promotion_candidates: List[Dict[str, Any]],
    lineage_packets: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Extend an existing AAL-Viz projection packet with sandbox summary.

    Returns:
        Extended projection packet. Immutable - creates a new dict.
    """
    extended = dict(base_packet)
    extended["sandbox_summary"] = build_sandbox_summary(
        adaptive_branches,
        replay_packets,
        stabilization_packets,
        promotion_candidates,
        lineage_packets,
    )

    # Recompute packet hash
    canonical = json.dumps(extended, sort_keys=True).encode("utf-8")
    extended["packet_hash"] = sha256(canonical).hexdigest()

    return extended
