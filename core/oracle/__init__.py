"""core.oracle - Governed Oracle Intake (v2.0.6).

Provides deterministic, governed intake of source evidence into the oracle
pipeline. All operations are shadow-only, replayable, and provenance-bound.
"""
from __future__ import annotations

from core.oracle.intake import IntakeEnvelope, build_intake_envelope
from core.oracle.evidence import SourceEvidencePacket, build_evidence_packet
from core.oracle.normalization import IntakeNormalizationPacket, build_normalization_packet
from core.oracle.replay import IntakeReplayPacket, run_intake_replay
from core.oracle.conflicts import IntakeConflictPacket, build_conflict_packet
from core.oracle.lineage import IntakeLineagePacket, IntakeLineageNode, build_intake_lineage
from core.oracle.stabilization import IntakeStabilizationPacket, build_intake_stabilization_packet
from core.oracle.approvals import IntakeApprovalPacket, build_approval_packet
from core.oracle.runtime import OracleIntakeRun, run_oracle_intake

__all__ = [
    "IntakeEnvelope",
    "build_intake_envelope",
    "SourceEvidencePacket",
    "build_evidence_packet",
    "IntakeNormalizationPacket",
    "build_normalization_packet",
    "IntakeReplayPacket",
    "run_intake_replay",
    "IntakeConflictPacket",
    "build_conflict_packet",
    "IntakeLineagePacket",
    "IntakeLineageNode",
    "build_intake_lineage",
    "IntakeStabilizationPacket",
    "build_intake_stabilization_packet",
    "IntakeApprovalPacket",
    "build_approval_packet",
    "OracleIntakeRun",
    "run_oracle_intake",
]
