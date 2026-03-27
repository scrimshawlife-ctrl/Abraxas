from __future__ import annotations

from abx.meta.authorityOfChange import build_authority_of_change_records
from abx.meta.stewardshipInventory import build_stewardship_inventory
from abx.meta.stewardshipTransfers import build_stewardship_transfer_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def classify_stewardship_roles() -> dict[str, list[str]]:
    buckets = {
        "canonical_steward": [],
        "delegated_steward": [],
        "reviewer_advisor": [],
        "proposer": [],
        "emergency_steward": [],
        "unknown": [],
    }
    for rec in build_stewardship_inventory():
        buckets.setdefault(rec.steward_role.replace("-", "_"), []).append(rec.steward_id)
    for ids in buckets.values():
        ids.sort()
    return buckets


def detect_hidden_meta_authority() -> list[dict[str, str]]:
    return [
        {"changeId": x.change_id, "reason": "unknown_approver"}
        for x in build_authority_of_change_records()
        if x.approver_role == "unknown"
    ]


def build_stewardship_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "StewardshipAudit.v1",
        "artifactId": "stewardship-audit",
        "stewards": [x.__dict__ for x in build_stewardship_inventory()],
        "authority": [x.__dict__ for x in build_authority_of_change_records()],
        "transfers": build_stewardship_transfer_records(),
        "classification": classify_stewardship_roles(),
        "hiddenAuthority": detect_hidden_meta_authority(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
