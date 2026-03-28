from __future__ import annotations

from abx.outcome.effectRealizationInventory import build_effect_realization_inventory
from abx.outcome.types import EffectRealizationRecord, OutcomeVerificationRecord


def build_effect_realization_records() -> list[EffectRealizationRecord]:
    return [
        EffectRealizationRecord(realization_id=rid, action_ref=action_ref, realization_state=state, evidence_mode=mode)
        for rid, action_ref, state, mode in build_effect_realization_inventory()
    ]


def build_outcome_verification_records() -> list[OutcomeVerificationRecord]:
    mapping = {
        "act.deploy.schema-v2": ("VERIFIED", "direct runtime validation passed"),
        "act.notify.partner": ("ACK_CONFIRMED", "partner ack with correlation id"),
        "act.repair.cache": ("INFERRED", "metrics converged after repair"),
        "act.cleanup.tmp": ("REVERIFY_REQUIRED", "no direct observation"),
        "act.run.canary": ("REVERIFY_REQUIRED", "partial signal only"),
        "act.migrate.legacy": ("NOT_COMPUTABLE", "missing downstream telemetry"),
    }
    return [
        OutcomeVerificationRecord(
            verification_id=f"ver.{idx:03d}",
            action_ref=action_ref,
            verification_state=state,
            verification_reason=reason,
        )
        for idx, (action_ref, (state, reason)) in enumerate(mapping.items(), start=1)
    ]
