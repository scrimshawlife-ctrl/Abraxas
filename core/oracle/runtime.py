"""OracleIntakeRun.v1 - Governed oracle intake runtime engine.

Behavior:
- build intake envelopes
- normalize payloads deterministically
- generate evidence packets
- replay normalize deterministically
- detect conflicts
- generate stabilization packets
- generate approval packets

Writes:
  out/oracle/latest.json
  out/intake_conflicts/latest.json
  out/intake_approvals/latest.json
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import uuid

from pydantic import BaseModel

from core.models.governance import Authority
from core.oracle.intake import IntakeEnvelope, build_intake_envelope, hash_payload
from core.oracle.evidence import SourceEvidencePacket, build_evidence_packet
from core.oracle.normalization import IntakeNormalizationPacket, build_normalization_packet
from core.oracle.replay import IntakeReplayPacket, run_intake_replay
from core.oracle.conflicts import IntakeConflictPacket, build_conflict_packet, detect_duplicate_sources
from core.oracle.stabilization import (
    IntakeStabilizationPacket,
    build_intake_stabilization_packet,
)
from core.oracle.approvals import IntakeApprovalPacket, build_approval_packet

VALID_STATUSES = {"complete", "partial", "failed"}

_OUT_ORACLE = Path("out/oracle")
_OUT_CONFLICTS = Path("out/intake_conflicts")
_OUT_APPROVALS = Path("out/intake_approvals")


class OracleIntakeRun(BaseModel):
    schema_version: str = "OracleIntakeRun.v1"
    run_id: str
    intake_envelopes: List[Dict[str, Any]]
    evidence_packets: List[Dict[str, Any]]
    normalization_packets: List[Dict[str, Any]]
    replay_packets: List[Dict[str, Any]]
    conflict_packets: List[Dict[str, Any]]
    stabilization_packets: List[Dict[str, Any]]
    approval_packets: List[Dict[str, Any]]
    deterministic_run_hash: str
    authority: Authority
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")


def _packet_to_dict(packet: BaseModel) -> Dict[str, Any]:
    """Convert a Pydantic model to a JSON-serializable dict."""
    return json.loads(json.dumps(packet.model_dump()))


def _compute_run_hash(run_id: str, envelopes: List[Dict[str, Any]]) -> str:
    canonical = json.dumps(
        {
            "run_id": run_id,
            "envelope_hashes": sorted(e.get("raw_payload_hash", "") for e in envelopes),
        },
        sort_keys=True,
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def run_oracle_intake(
    source_payloads: List[Dict[str, Any]],
    authority: Authority,
    run_id: Optional[str] = None,
    out_dir: Optional[Path] = None,
) -> OracleIntakeRun:
    """Execute governed oracle intake pipeline.

    Args:
        source_payloads: List of dicts each with keys:
            - source_id: str
            - source_type: str
            - payload: Any  (raw payload data)
        authority: Locked Authority instance.
        run_id: Optional stable run ID. Auto-generated if None.
        out_dir: Optional output directory override.

    Returns:
        OracleIntakeRun with all intake artifacts.

    Writes:
        out/oracle/latest.json
        out/intake_conflicts/latest.json
        out/intake_approvals/latest.json
    """
    if not authority.is_locked():
        raise ValueError("authority must be locked")

    if run_id is None:
        run_id = str(uuid.uuid4())

    envelopes: List[IntakeEnvelope] = []
    evidence_pkts: List[SourceEvidencePacket] = []
    norm_pkts: List[IntakeNormalizationPacket] = []
    replay_pkts: List[IntakeReplayPacket] = []
    conflict_pkts: List[IntakeConflictPacket] = []
    stab_pkts: List[IntakeStabilizationPacket] = []
    approval_pkts: List[IntakeApprovalPacket] = []

    # Step 1: Build intake envelopes
    for idx, sp in enumerate(source_payloads):
        source_id = sp.get("source_id", f"src-{idx}")
        source_type = sp.get("source_type", "document")
        raw_payload = sp.get("payload", {})

        envelope = build_intake_envelope(
            intake_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{run_id}-intake-{idx}")),
            source_id=source_id,
            source_type=source_type,
            intake_timestamp_index=idx,
            raw_payload=raw_payload,
            authority=authority,
        )
        envelopes.append(envelope)

    # Step 2: Normalize payloads deterministically
    for envelope in envelopes:
        raw_payload = next(
            (sp.get("payload", {}) for i, sp in enumerate(source_payloads)
             if str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{run_id}-intake-{i}")) == envelope.intake_id),
            {}
        )
        norm_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{run_id}-norm-{envelope.intake_id}"))
        norm_pkt = build_normalization_packet(
            normalization_id=norm_id,
            source_hash=envelope.raw_payload_hash,
            raw_payload=raw_payload,
            authority=authority,
        )
        norm_pkts.append(norm_pkt)

        # Build evidence packet
        ev_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{run_id}-ev-{envelope.intake_id}"))
        ev_pkt = build_evidence_packet(
            evidence_id=ev_id,
            intake_hash=envelope.envelope_hash(),
            source_hash=envelope.raw_payload_hash,
            evidence_type="structural",
            authority=authority,
        )
        evidence_pkts.append(ev_pkt)

    # Step 3: Replay normalize deterministically (self-replay: source == replay)
    for i, (envelope, norm_pkt) in enumerate(zip(envelopes, norm_pkts)):
        replay_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{run_id}-replay-{i}"))
        envelope_hash = envelope.envelope_hash()
        replay_pkt = run_intake_replay(
            source_intake_hash=envelope_hash,
            replay_intake_hash=envelope_hash,
            replay_id=replay_id,
            authority=authority,
            source_normalization_hash=norm_pkt.deterministic_normalization_hash,
            replay_normalization_hash=norm_pkt.deterministic_normalization_hash,
        )
        replay_pkts.append(replay_pkt)

    # Step 4: Detect conflicts
    all_source_hashes = [e.raw_payload_hash for e in envelopes]
    duplicates = detect_duplicate_sources(all_source_hashes)
    if duplicates:
        conflict_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{run_id}-conflict-dup"))
        conflict_pkt = build_conflict_packet(
            conflict_id=conflict_id,
            conflicting_source_hashes=duplicates,
            conflict_type="duplicate_source",
            authority=authority,
            severity="low",
            resolution_required=False,
        )
        conflict_pkts.append(conflict_pkt)

    # Step 5: Generate stabilization packets
    replay_matches = sum(1 for p in replay_pkts if p.deterministic_match)
    replay_failures = sum(1 for p in replay_pkts if not p.deterministic_match)
    unresolved_conflict_count = sum(
        1 for c in conflict_pkts if c.status == "unresolved"
    )

    for i, envelope in enumerate(envelopes):
        stab_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{run_id}-stab-{i}"))
        stab_pkt = build_intake_stabilization_packet(
            stabilization_id=stab_id,
            intake_hash=envelope.envelope_hash(),
            replay_match_count=replay_matches,
            replay_failure_count=replay_failures,
            conflict_count=unresolved_conflict_count,
            authority=authority,
        )
        stab_pkts.append(stab_pkt)

    # Step 6: Generate approval packets
    conflict_hash_list = [c.conflict_hash() for c in conflict_pkts if c.status == "unresolved"]
    for i, (envelope, stab_pkt) in enumerate(zip(envelopes, stab_pkts)):
        appr_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{run_id}-appr-{i}"))
        appr_pkt = build_approval_packet(
            approval_id=appr_id,
            intake_hash=envelope.envelope_hash(),
            stabilization_hash=stab_pkt.stabilization_hash(),
            conflict_hashes=conflict_hash_list,
            authority=authority,
            approved=False,  # operator review required
        )
        approval_pkts.append(appr_pkt)

    # Build run hash
    envelope_dicts = [_packet_to_dict(e) for e in envelopes]
    run_hash = _compute_run_hash(run_id, envelope_dicts)

    overall_status = "complete"
    if any(p.status == "failed" for p in stab_pkts):
        overall_status = "partial"
    if not envelopes:
        overall_status = "failed"

    oracle_run = OracleIntakeRun(
        run_id=run_id,
        intake_envelopes=envelope_dicts,
        evidence_packets=[_packet_to_dict(p) for p in evidence_pkts],
        normalization_packets=[_packet_to_dict(p) for p in norm_pkts],
        replay_packets=[_packet_to_dict(p) for p in replay_pkts],
        conflict_packets=[_packet_to_dict(p) for p in conflict_pkts],
        stabilization_packets=[_packet_to_dict(p) for p in stab_pkts],
        approval_packets=[_packet_to_dict(p) for p in approval_pkts],
        deterministic_run_hash=run_hash,
        authority=authority,
        status=overall_status,
    )

    # Write artifacts
    base_dir = out_dir or Path(".")
    _write_artifact(base_dir / "out/oracle", "latest.json", _packet_to_dict(oracle_run))
    _write_artifact(
        base_dir / "out/intake_conflicts",
        "latest.json",
        {"run_id": run_id, "conflicts": [_packet_to_dict(c) for c in conflict_pkts]},
    )
    _write_artifact(
        base_dir / "out/intake_approvals",
        "latest.json",
        {"run_id": run_id, "approvals": [_packet_to_dict(a) for a in approval_pkts]},
    )
    _write_artifact(
        base_dir / "out/intake_stabilization",
        "latest.json",
        {"run_id": run_id, "stabilizations": [_packet_to_dict(s) for s in stab_pkts]},
    )

    return oracle_run


def _write_artifact(directory: Path, filename: str, data: Any) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(json.dumps(data, indent=2), encoding="utf-8")
