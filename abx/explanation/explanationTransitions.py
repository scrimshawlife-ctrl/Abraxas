from __future__ import annotations

from abx.explanation.types import ExplanationTransitionRecord


def build_explanation_transition_records() -> tuple[ExplanationTransitionRecord, ...]:
    return (
        ExplanationTransitionRecord(
            "trn.summary.loss",
            "executive.summary",
            "COMPRESSED_WITH_PRESERVATION",
            "COMPRESSION_LOSS_ACTIVE",
            "uncertainty_clause_removed",
            "TRUST_DOWNGRADED",
        ),
        ExplanationTransitionRecord(
            "trn.card.omission",
            "dashboard.card",
            "INTERPRETIVELY_COMPRESSED_BUT_HONEST",
            "CAVEAT_OMISSION_ACTIVE",
            "card_truncation",
            "TRUST_DOWNGRADED",
        ),
        ExplanationTransitionRecord(
            "trn.causal.block",
            "causal.summary",
            "INFERRED_LAYER",
            "BOUNDARY_BLOCK_ACTIVE",
            "causal_support_insufficient",
            "BLOCKED",
        ),
        ExplanationTransitionRecord(
            "trn.refresh",
            "operator.writeup",
            "CAVEAT_OMISSION_ACTIVE",
            "HONESTY_RESTORED",
            "caveat_reintroduced",
            "TRUST_STABLE",
        ),
    )
