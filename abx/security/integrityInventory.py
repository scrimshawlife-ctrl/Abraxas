from __future__ import annotations

from abx.security.types import IntegrityVerificationRecord, TamperResistanceRecord


def build_integrity_inventory() -> list[IntegrityVerificationRecord]:
    return [
        IntegrityVerificationRecord(
            verification_id="int.report.audit_hash",
            target_surface="observability.summary_assembly",
            artifact_class="report",
            verification_mode="hash_match",
            status="verified",
            owner="observability",
        ),
        IntegrityVerificationRecord(
            verification_id="int.deployment.config_boundary",
            target_surface="deployment.config_inventory",
            artifact_class="config",
            verification_mode="classification_gate",
            status="governed_unchecked",
            owner="deployment",
        ),
        IntegrityVerificationRecord(
            verification_id="int.policy.override_records",
            target_surface="governance.override_inventory",
            artifact_class="policy_override",
            verification_mode="precedence_validation",
            status="monitored",
            owner="governance",
        ),
        IntegrityVerificationRecord(
            verification_id="int.federation.handoff_lineage",
            target_surface="federation.handoff_envelopes",
            artifact_class="handoff_contract",
            verification_mode="lineage_correlation",
            status="heuristic",
            owner="federation",
        ),
        IntegrityVerificationRecord(
            verification_id="int.legacy.import_bridge",
            target_surface="legacy.import_bridge.direct_adapter",
            artifact_class="adapter",
            verification_mode="none",
            status="not_computable",
            owner="integration",
        ),
    ]


def build_tamper_resistance_inventory() -> list[TamperResistanceRecord]:
    return [
        TamperResistanceRecord(
            tamper_id="tamper.audit_hash_chain",
            target_surface="governance.scorecard_bundle",
            protection_class="tamper_evidence",
            resistance_level="governed",
            mismatch_signal="hash_mismatch",
            owner="governance",
        ),
        TamperResistanceRecord(
            tamper_id="tamper.override_precedence",
            target_surface="governance.override_precedence.evaluate",
            protection_class="precedence_lock",
            resistance_level="governed",
            mismatch_signal="precedence_violation",
            owner="governance",
        ),
        TamperResistanceRecord(
            tamper_id="tamper.legacy_bridge",
            target_surface="legacy.import_bridge.direct_adapter",
            protection_class="legacy_exposure",
            resistance_level="partial",
            mismatch_signal="untracked_mutation",
            owner="integration",
        ),
    ]
