"""Warden-post — spec v1.1 gate after Weave, before Keep."""

from __future__ import annotations

from typing import Any

from abx_familiar.ir.delivery_pack_v0 import AttachmentRef
from abx_familiar.ir.ward_report_v0 import WardFlag, WardReport

REQUIRED_KINDS = {"evidence", "receipt", "ward_report", "binding"}


def _flag(code: str, message: str, severity: str, **meta: Any) -> WardFlag:
    return WardFlag(code=code, message=message, severity=severity, meta=dict(meta))


def warden_post(
    binding: dict[str, Any],
    attachments: list[AttachmentRef],
    *,
    report_id: str = "ward_post_unspecified",
) -> WardReport:
    violations: list[WardFlag] = []
    if binding.get("status") != "BOUND_SHADOW":
        violations.append(
            _flag("NOT_BOUND", "Warden-post requires BOUND_SHADOW", "error", got=str(binding.get("status")))
        )
    if binding.get("lane") != "SHADOW":
        violations.append(_flag("LANE_LEAK", "binding lane must be SHADOW", "error"))
    kinds = {a.kind for a in attachments}
    missing = sorted(REQUIRED_KINDS - kinds)
    if missing:
        violations.append(_flag("WEAVE_INCOMPLETE", "weave missing attachment kinds", "error", missing=missing))
    passed = len(violations) == 0
    return WardReport(
        report_id=report_id,
        violations=violations,
        warnings=[],
        tier_leakage_flags=[],
        drift_class="none" if passed else "structural",
        invariance_passed=passed,
        not_computable=False,
        missing_fields=[],
    )
