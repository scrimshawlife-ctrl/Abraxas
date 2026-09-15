"""Warden-pre — spec v1.1 gate before Binder.

Sequence: Summoner → Warden pre → Forager → Binder → …
This module only flags. It does not mutate the pack or grant authority.
"""

from __future__ import annotations

from typing import Any

from abx_familiar.ir.evidence_pack_v0 import EvidencePack
from abx_familiar.ir.ward_report_v0 import WardFlag, WardReport

SCHEMA = "FamiliarIngestionReceipt.v0"
REQUIRED_FALSE = (
    "execution_authority",
    "promotion_authorized",
    "forecast_routing_authorized",
    "canon_mutation_allowed",
)


def _flag(code: str, message: str, severity: str, **meta: Any) -> WardFlag:
    return WardFlag(code=code, message=message, severity=severity, meta=dict(meta))


def warden_pre(
    pack: EvidencePack | None,
    receipt: dict[str, Any] | None,
    *,
    report_id: str = "ward_pre_unspecified",
) -> WardReport:
    violations: list[WardFlag] = []
    warnings: list[WardFlag] = []
    leakage: list[str] = []
    missing: list[str] = []

    if pack is None:
        missing.append("pack")
        violations.append(_flag("NO_PACK", "Warden-pre requires an EvidencePack", "error"))
    else:
        try:
            pack.validate()
        except ValueError as exc:
            violations.append(
                _flag("INVALID_PACK", str(exc), "error")
            )

    if receipt is None:
        missing.append("receipt")
        violations.append(_flag("NO_RECEIPT", "Warden-pre requires a receipt", "error"))
        return WardReport(
            report_id=report_id,
            violations=violations,
            warnings=warnings,
            tier_leakage_flags=leakage,
            drift_class="structural",
            invariance_passed=False,
            not_computable=True,
            missing_fields=missing,
        )

    if receipt.get("schema_version") != SCHEMA:
        violations.append(
            _flag(
                "BAD_SCHEMA",
                f"schema_version must be {SCHEMA}",
                "error",
                got=str(receipt.get("schema_version")),
            )
        )
    if receipt.get("lane") != "SHADOW":
        leakage.append("lane")
        violations.append(
            _flag("LANE_LEAK", "lane must be SHADOW", "error", got=str(receipt.get("lane")))
        )
    if receipt.get("advisory_only") is not True:
        leakage.append("advisory_only")
        violations.append(_flag("ADVISORY_REQUIRED", "advisory_only must be true", "error"))
    if receipt.get("commercial_claims_blocked") is not True:
        leakage.append("commercial_claims")
        violations.append(
            _flag("COMMERCIAL_UNBLOCKED", "commercial_claims_blocked must be true", "error")
        )

    authority = receipt.get("authority") if isinstance(receipt.get("authority"), dict) else {}
    for key in REQUIRED_FALSE:
        if authority.get(key) is not False:
            leakage.append(key)
            violations.append(
                _flag("AUTHORITY_LEAK", f"{key} must be false", "error", field=key)
            )

    status = receipt.get("status")
    if status != "INGESTED_SHADOW":
        violations.append(
            _flag(
                "NOT_SHADOW_INGEST",
                "status must be INGESTED_SHADOW before Binder",
                "error",
                got=str(status),
            )
        )

    if int(receipt.get("claim_count") or 0) != 0:
        warnings.append(
            _flag(
                "CLAIMS_ON_LOCAL_IR",
                "local EvidencePack IR has no claims; claim_count should be 0",
                "warn",
                claim_count=receipt.get("claim_count"),
            )
        )

    if pack is not None and receipt.get("pack_id") and receipt.get("pack_id") != pack.pack_id:
        violations.append(
            _flag(
                "PACK_ID_MISMATCH",
                "receipt.pack_id does not match pack.pack_id",
                "error",
                pack_id=pack.pack_id,
                receipt_pack_id=receipt.get("pack_id"),
            )
        )

    passed = len(violations) == 0
    if leakage and not passed:
        drift = "critical" if "execution_authority" in leakage else "structural"
    elif warnings and passed:
        drift = "benign"
    else:
        drift = "none" if passed else "structural"

    return WardReport(
        report_id=report_id,
        violations=violations,
        warnings=warnings,
        tier_leakage_flags=leakage,
        drift_class=drift,
        invariance_passed=passed,
        not_computable=bool(missing),
        missing_fields=missing,
    )
