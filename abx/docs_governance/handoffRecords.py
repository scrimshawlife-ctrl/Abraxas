from __future__ import annotations

from abx.docs_governance.types import HandoffRecord


def build_handoff_records() -> list[HandoffRecord]:
    return [
        HandoffRecord("handoff.ops.shift", "operator", "operator", "shift_packet", "complete_handoff", "low"),
        HandoffRecord("handoff.maintainer.transfer", "maintainer", "future_owner", "ownership_transfer", "partial_handoff", "medium"),
        HandoffRecord("handoff.incident.followup", "incident_responder", "maintainer", "incident_followup", "complete_handoff", "low"),
        HandoffRecord("handoff.legacy.bridge", "integration", "future_owner", "legacy_transfer", "stale_handoff", "high"),
    ]
