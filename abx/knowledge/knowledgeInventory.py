from __future__ import annotations

from abx.knowledge.types import ActiveVsHistoricalClassificationRecord, KnowledgeSurfaceRecord


def build_knowledge_inventory() -> list[KnowledgeSurfaceRecord]:
    rows = [
        KnowledgeSurfaceRecord("knowledge.baseline.manifest", "authoritative_active", "governance", True),
        KnowledgeSurfaceRecord("knowledge.continuity.summary", "governed_derived", "operations", True),
        KnowledgeSurfaceRecord("knowledge.incident.history", "historical_record", "operations", False),
        KnowledgeSurfaceRecord("knowledge.scorecards.archive", "archival", "governance", False),
        KnowledgeSurfaceRecord("knowledge.operator.notes", "stale_candidate", "operations", False),
    ]
    return sorted(rows, key=lambda x: x.surface_id)


def classify_active_vs_historical() -> list[ActiveVsHistoricalClassificationRecord]:
    rows: list[ActiveVsHistoricalClassificationRecord] = []
    for item in build_knowledge_inventory():
        state = "ACTIVE" if item.classification in {"authoritative_active", "governed_derived"} else "HISTORICAL"
        rows.append(ActiveVsHistoricalClassificationRecord(surface_id=item.surface_id, activity_state=state))
    return sorted(rows, key=lambda x: x.surface_id)
