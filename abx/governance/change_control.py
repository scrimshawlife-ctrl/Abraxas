from __future__ import annotations

from pathlib import Path
from typing import Any

from abx.governance.canonical_manifest import build_canonical_manifest
from abx.governance.migration_guards import run_migration_guards
from abx.governance.types import ChangeControlRequestArtifact
from abx.governance.waivers import build_waiver_audit
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_change_control_request(payload: dict[str, Any]) -> ChangeControlRequestArtifact:
    request_id = str(payload.get("request_id") or "CCR-UNSET")
    changed_paths = sorted(str(x) for x in list(payload.get("changed_paths") or []))

    manifest = build_canonical_manifest()
    members = manifest.members
    affected_surfaces = sorted(
        {
            m["member_id"]
            for m in members
            if any(token in m["surface"] or token in m["member_id"] for token in changed_paths)
        }
    )

    guards = run_migration_guards()
    waiver_audit = build_waiver_audit()
    active_checks = {
        c
        for row in waiver_audit.active_waivers
        for c in row.get("related_checks", [])
    }

    required_evidence = [
        "run_baseline_enforcement",
        "run_migration_guards",
        "run_breaking_change_scan",
        "targeted_tests",
    ]

    if guards.status == "BREAKING":
        change_type = "breaking"
        risk_status = "BREAKING"
    elif guards.status == "MIGRATION_REQUIRED":
        change_type = "migration-required"
        risk_status = "MIGRATION_REQUIRED"
    elif affected_surfaces:
        change_type = "additive-safe"
        risk_status = "ADDITIVE_SAFE"
    else:
        change_type = "internal-only"
        risk_status = "INTERNAL_ONLY"

    waiver_required = risk_status in {"MIGRATION_REQUIRED", "BREAKING"} and not bool(active_checks)

    req_payload = {
        "request_id": request_id,
        "change_type": change_type,
        "affected_surfaces": affected_surfaces,
        "required_evidence": required_evidence,
        "waiver_required": waiver_required,
        "risk_status": risk_status,
    }
    request_hash = sha256_bytes(dumps_stable(req_payload).encode("utf-8"))

    return ChangeControlRequestArtifact(
        artifact_type="ChangeControlRequestArtifact.v1",
        artifact_id=f"change-control-{request_id}",
        request_id=request_id,
        change_type=change_type,
        affected_surfaces=affected_surfaces,
        required_evidence=required_evidence,
        waiver_required=waiver_required,
        risk_status=risk_status,
        request_hash=request_hash,
    )


def build_change_impact_summary(payload: dict[str, Any]) -> dict[str, Any]:
    req = build_change_control_request(payload)
    return {
        "request": req.__dict__,
        "checks": {
            "must_pass": ["baseline_enforcement", "migration_guards", "breaking_scan"],
            "may_require_waiver": req.waiver_required,
        },
    }
