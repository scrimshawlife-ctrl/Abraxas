from __future__ import annotations

from abx.governance.decision_types import OverrideRecord


def build_override_inventory() -> list[OverrideRecord]:
    rows = [
        OverrideRecord(
            override_id="override.incident.rollback",
            override_type="waiver_backed_exception",
            owner="operations",
            reason="incident containment",
            scope="incident-triage",
            duration="temporary",
            target_policy="policy.boundary.trust",
        ),
        OverrideRecord(
            override_id="override.emergency.block-external",
            override_type="emergency_override",
            owner="governance",
            reason="external feed instability",
            scope="boundary-ingest",
            duration="temporary",
            target_policy="policy.boundary.validation",
        ),
    ]
    return sorted(rows, key=lambda x: x.override_id)
