from __future__ import annotations

from abx.outcome.types import OutcomeVerificationRecord


def build_outcome_transition_records() -> list[OutcomeVerificationRecord]:
    return [
        OutcomeVerificationRecord("trv.001", "act.deploy.schema-v2", "ACTION_COMPLETED", "execution pipeline finished"),
        OutcomeVerificationRecord("trv.002", "act.deploy.schema-v2", "EFFECT_OBSERVED", "runtime behavior verified"),
        OutcomeVerificationRecord("trv.003", "act.notify.partner", "EFFECT_ACKNOWLEDGED", "partner callback received"),
        OutcomeVerificationRecord("trv.004", "act.repair.cache", "EFFECT_PARTIAL", "subset verified"),
        OutcomeVerificationRecord("trv.005", "act.notify.partner", "EFFECT_DELAYED", "downstream pending"),
        OutcomeVerificationRecord("trv.006", "act.cleanup.tmp", "EFFECT_ABSENT", "no outcome evidence"),
        OutcomeVerificationRecord("trv.007", "act.run.canary", "OUTCOME_CONTRADICTORY", "signals disagree"),
        OutcomeVerificationRecord("trv.008", "act.migrate.legacy", "VERIFICATION_REQUIRED", "insufficient evidence"),
    ]
