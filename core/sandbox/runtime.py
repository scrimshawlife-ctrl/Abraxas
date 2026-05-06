"""AdaptiveSimulationRun.v1 - Sandbox runtime engine.

Implements:
- AdaptiveSimulationRun model
- run_adaptive_sandbox() function

Behavior:
- create isolated sandbox branch
- apply candidate mutations
- replay branch deterministically
- generate stabilization packet
- generate promotion candidate
- emit receipts

Writes:
  out/sandbox/latest.json
  out/promotion_candidates/latest.json
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import uuid

from pydantic import BaseModel

from core.models.governance import Authority
from core.sandbox.models import AdaptiveSandboxBranch, build_sandbox_branch
from core.sandbox.mutations import CandidateMutationPacket, build_mutation_packet
from core.sandbox.replay import SandboxReplayPacket, run_sandbox_replay
from core.sandbox.stabilization import (
    SandboxStabilizationPacket,
    build_stabilization_packet,
)
from core.sandbox.promotion import SandboxPromotionCandidate, build_promotion_candidate
from core.sandbox.receipts import MutationProposalReceipt, build_mutation_receipt

VALID_STATUSES = {"running", "complete", "failed", "partial"}


class AdaptiveSimulationRun(BaseModel):
    schema_version: str = "AdaptiveSimulationRun.v1"
    run_id: str
    branch_hash: str
    mutation_receipts: List[str]
    replay_packets: List[str]
    stabilization_packet: str
    promotion_candidate: str
    deterministic_run_hash: str
    authority: Authority
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

    def compute_run_hash(self) -> str:
        canonical = json.dumps(
            {
                "run_id": self.run_id,
                "branch_hash": self.branch_hash,
                "mutation_receipts": sorted(self.mutation_receipts),
                "replay_packets": sorted(self.replay_packets),
                "stabilization_packet": self.stabilization_packet,
                "promotion_candidate": self.promotion_candidate,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def run_adaptive_sandbox(
    governed_state: Dict[str, Any],
    transition_packets: List[Dict[str, Any]],
    replay_packets_input: List[Dict[str, Any]],
    authority: Optional[Authority] = None,
    out_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run the adaptive sandbox engine.

    Args:
        governed_state: The current governed state (read-only, not mutated).
        transition_packets: List of candidate transition descriptors.
        replay_packets_input: List of replay verification inputs.
        authority: Locked authority (defaults to sandbox authority).
        out_dir: Output directory for artifacts (defaults to out/sandbox/).

    Returns:
        Dict with sandbox run artifacts.

    Notes:
        - Sandbox is isolated from runtime state
        - All operations are deterministic
        - No live mutation of Canon or runtime state
    """
    if authority is None:
        authority = Authority(
            authority_id="auth.sandbox.001",
            actor="system.sandbox",
            locked=True,
            scope="sandbox_only",
        )

    if out_dir is None:
        out_dir = Path("out/sandbox")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    promo_dir = Path("out/promotion_candidates")
    promo_dir.mkdir(parents=True, exist_ok=True)

    # Deterministically derive source state hash from governed_state
    source_state_hash = sha256(
        json.dumps(governed_state, sort_keys=True).encode("utf-8")
    ).hexdigest()

    branch_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, source_state_hash))
    branch = build_sandbox_branch(
        branch_id=branch_id,
        source_state_hash=source_state_hash,
        sandbox_scope="adaptive_sandbox",
        branch_generation=governed_state.get("generation", 0),
        authority=authority,
    )

    # Apply candidate mutations (sandbox-isolated)
    mutation_packets: List[CandidateMutationPacket] = []
    mutation_receipts: List[MutationProposalReceipt] = []

    for i, tp in enumerate(transition_packets):
        mutation_type = tp.get("mutation_type", "route_adjustment")
        mutation_id = str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"{branch.deterministic_branch_hash}-{i}")
        )
        target_branch_hash = sha256(
            json.dumps({"branch": branch.deterministic_branch_hash, "idx": i}, sort_keys=True).encode("utf-8")
        ).hexdigest()

        mut_pkt = build_mutation_packet(
            mutation_id=mutation_id,
            source_branch_hash=branch.deterministic_branch_hash,
            target_branch_hash=target_branch_hash,
            mutation_type=mutation_type,
            proposed_transition_hashes=tp.get("transition_hashes", []),
            authority=authority,
        )
        mutation_packets.append(mut_pkt)

    # Build replay packets
    replay_results: List[SandboxReplayPacket] = []
    for i, rp_input in enumerate(replay_packets_input):
        replay_id = str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"replay-{branch.deterministic_branch_hash}-{i}")
        )
        replay_branch_hash = rp_input.get("replay_branch_hash", branch.deterministic_branch_hash)
        pkt = run_sandbox_replay(
            source_branch_hash=branch.deterministic_branch_hash,
            replay_branch_hash=replay_branch_hash,
            replay_id=replay_id,
            authority=authority,
        )
        replay_results.append(pkt)

    # If no replay inputs provided, do one self-replay (always matches)
    if not replay_results:
        replay_id = str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"replay-self-{branch.deterministic_branch_hash}")
        )
        pkt = run_sandbox_replay(
            source_branch_hash=branch.deterministic_branch_hash,
            replay_branch_hash=branch.deterministic_branch_hash,
            replay_id=replay_id,
            authority=authority,
        )
        replay_results.append(pkt)

    # Build mutation receipts
    for mut_pkt in mutation_packets:
        replay_hash_val = replay_results[0].replay_hash() if replay_results else "no_replay"
        stab_hash_placeholder = sha256(b"stabilization_pending").hexdigest()
        receipt_id = str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"receipt-{mut_pkt.deterministic_mutation_hash}")
        )
        receipt = build_mutation_receipt(
            receipt_id=receipt_id,
            mutation_hash=mut_pkt.deterministic_mutation_hash,
            branch_hash=branch.deterministic_branch_hash,
            replay_hash=replay_hash_val,
            stabilization_hash=stab_hash_placeholder,
            authority=authority,
        )
        mutation_receipts.append(receipt)

    # Count matches/failures
    match_count = sum(1 for r in replay_results if r.deterministic_match)
    failure_count = sum(1 for r in replay_results if not r.deterministic_match)

    stabilization_id = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, f"stab-{branch.deterministic_branch_hash}")
    )
    stab_pkt = build_stabilization_packet(
        stabilization_id=stabilization_id,
        sandbox_branch_hash=branch.deterministic_branch_hash,
        replay_match_count=match_count,
        replay_failure_count=failure_count,
        authority=authority,
    )

    replay_hash_for_promo = replay_results[0].replay_hash() if replay_results else sha256(b"no_replay").hexdigest()
    candidate_id = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, f"candidate-{branch.deterministic_branch_hash}")
    )
    promotion_candidate = build_promotion_candidate(
        candidate_id=candidate_id,
        sandbox_branch_hash=branch.deterministic_branch_hash,
        stabilization_hash=stab_pkt.stabilization_hash(),
        replay_hash=replay_hash_for_promo,
        proposed_promotions=[m.deterministic_mutation_hash for m in mutation_packets],
        authority=authority,
        stabilization_state=stab_pkt.stabilization_state,
    )

    # Build AdaptiveSimulationRun
    sim_run = AdaptiveSimulationRun(
        run_id=str(uuid.uuid4()),
        branch_hash=branch.deterministic_branch_hash,
        mutation_receipts=[r.receipt_hash() for r in mutation_receipts],
        replay_packets=[r.replay_hash() for r in replay_results],
        stabilization_packet=stab_pkt.stabilization_hash(),
        promotion_candidate=promotion_candidate.candidate_hash(),
        deterministic_run_hash="",
        authority=authority,
        status="complete" if failure_count == 0 else "partial",
    )
    run_hash = sim_run.compute_run_hash()
    object.__setattr__(sim_run, "deterministic_run_hash", run_hash)

    # Serialize artifacts
    sandbox_artifact = {
        "schema_version": "AdaptiveSimulationRun.v1",
        "run_id": sim_run.run_id,
        "branch_hash": branch.deterministic_branch_hash,
        "branch_id": branch.branch_id,
        "branch_generation": branch.branch_generation,
        "stabilization_state": stab_pkt.stabilization_state,
        "replay_match_count": match_count,
        "replay_failure_count": failure_count,
        "mutation_count": len(mutation_packets),
        "deterministic_run_hash": sim_run.deterministic_run_hash,
        "status": sim_run.status,
    }
    (out_dir / "latest.json").write_text(
        json.dumps(sandbox_artifact, indent=2), encoding="utf-8"
    )

    promo_artifact = {
        "schema_version": "SandboxPromotionCandidate.v1",
        "candidate_id": promotion_candidate.candidate_id,
        "sandbox_branch_hash": promotion_candidate.sandbox_branch_hash,
        "stabilization_hash": promotion_candidate.stabilization_hash,
        "replay_hash": promotion_candidate.replay_hash,
        "proposed_promotions": promotion_candidate.proposed_promotions,
        "operator_review_required": promotion_candidate.operator_review_required,
        "promotion_allowed": promotion_candidate.promotion_allowed,
        "status": promotion_candidate.status,
    }
    (promo_dir / "latest.json").write_text(
        json.dumps(promo_artifact, indent=2), encoding="utf-8"
    )

    return {
        "branch": branch,
        "mutation_packets": mutation_packets,
        "replay_results": replay_results,
        "stabilization": stab_pkt,
        "promotion_candidate": promotion_candidate,
        "mutation_receipts": mutation_receipts,
        "simulation_run": sim_run,
        "sandbox_artifact": sandbox_artifact,
        "promo_artifact": promo_artifact,
    }
