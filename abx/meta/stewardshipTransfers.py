from __future__ import annotations


def build_stewardship_transfer_records() -> list[dict[str, str]]:
    return [
        {
            "transferId": "transfer-2026q1-canon",
            "fromRole": "canonical-steward",
            "toRole": "delegated-steward",
            "status": "completed",
            "handoffRef": "handoff:canon:2026q1",
        },
        {
            "transferId": "transfer-2026q1-shadow",
            "fromRole": "unknown",
            "toRole": "delegated-steward",
            "status": "blocked",
            "handoffRef": "handoff:missing",
        },
    ]
