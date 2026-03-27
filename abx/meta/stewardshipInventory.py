from __future__ import annotations

from abx.meta.types import StewardshipRecord


def build_stewardship_inventory() -> list[StewardshipRecord]:
    return [
        StewardshipRecord(
            steward_id="stew-canon",
            steward_role="canonical-steward",
            domains=["governance", "evolution"],
            authority_level="primary",
            status="active",
        ),
        StewardshipRecord(
            steward_id="stew-meta-ops",
            steward_role="delegated-steward",
            domains=["governance"],
            authority_level="delegated",
            status="active",
        ),
        StewardshipRecord(
            steward_id="stew-security-review",
            steward_role="reviewer-advisor",
            domains=["security", "governance"],
            authority_level="review",
            status="active",
        ),
        StewardshipRecord(
            steward_id="stew-shadow",
            steward_role="unknown",
            domains=["governance"],
            authority_level="unknown",
            status="partial",
        ),
    ]
