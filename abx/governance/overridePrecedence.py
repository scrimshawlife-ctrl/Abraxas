from __future__ import annotations

from abx.governance.decision_types import OverridePrecedenceRecord


def build_override_precedence() -> OverridePrecedenceRecord:
    order = [
        "authoritative_policy",
        "waiver_backed_exception",
        "emergency_override",
        "legacy_exception",
        "hidden_override_prohibited",
    ]
    return OverridePrecedenceRecord(
        precedence_id="override-precedence-v1",
        order=order,
        hidden_override_detected=False,
    )
