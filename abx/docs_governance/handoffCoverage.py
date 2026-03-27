from __future__ import annotations

from abx.docs_governance.handoffClassification import classify_handoff_completeness
from abx.docs_governance.types import KnowledgeTransferCoverageRecord


def build_handoff_coverage() -> list[KnowledgeTransferCoverageRecord]:
    cls = classify_handoff_completeness()
    return [
        KnowledgeTransferCoverageRecord("coverage.handoff.complete", "handoff_completeness", "maintained", cls["complete_handoff"]),
        KnowledgeTransferCoverageRecord("coverage.handoff.gaps", "handoff_gap_visibility", "partial" if cls["partial_handoff"] else "maintained", cls["partial_handoff"] + cls["stale_handoff"]),
    ]
