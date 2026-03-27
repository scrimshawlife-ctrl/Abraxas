from __future__ import annotations

from abx.decision.decisionRecords import build_decision_records
from abx.util.jsonutil import dumps_stable


def serialize_decisions(run_id: str = "RUN-DECISION") -> str:
    rows = [
        x.__dict__ | {"outcome": x.outcome.__dict__}
        for x in build_decision_records(run_id=run_id)
    ]
    return dumps_stable(rows)
