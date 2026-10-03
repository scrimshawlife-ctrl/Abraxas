from __future__ import annotations

from abx.evidence.types import BurdenOfProofRecord


def build_burden_inventory() -> tuple[BurdenOfProofRecord, ...]:
    return (
        BurdenOfProofRecord("bur.release.001", "RELEASE_DECISION", "proposer.release", "STRONG", 0.82),
        BurdenOfProofRecord("bur.override.001", "POLICY_EXCEPTION", "proposer.override", "VERY_STRONG", 0.55),
        BurdenOfProofRecord("bur.rollback.001", "ROLLBACK_DECISION", "proposer.reliability", "MODERATE", 0.62),
        BurdenOfProofRecord("bur.publish.001", "PUBLICATION_DECISION", "proposer.comms", "STRONG", 0.68),
        BurdenOfProofRecord("bur.tuning.001", "LOW_RISK_TUNING", "proposer.runtime", "LIGHT", 0.51),
    )
