from __future__ import annotations

from abx.continuity.planClassification import classify_plan_state
from abx.continuity.planInventory import build_plan_inventory
from abx.continuity.planningHorizons import build_planning_horizons
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_long_horizon_plan_report() -> dict[str, object]:
    plans = build_plan_inventory()
    horizons = {x.mission_id: x for x in build_planning_horizons()}
    classified = {
        row.plan_id: classify_plan_state(plan_state=row.plan_state, viability_state=horizons[row.mission_id].viability_state)
        for row in plans
    }
    report = {
        "artifactType": "LongHorizonPlanAudit.v1",
        "artifactId": "long-horizon-plan-audit",
        "plans": [x.__dict__ for x in plans],
        "horizons": [x.__dict__ for x in build_planning_horizons()],
        "planStates": classified,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
