"""
WardReport.v0

Deterministic, hashable container for governance findings produced by the Warden.

Rules:
- Flags only. No payload mutation. No suppression.
- Used for auditability and promotion gating.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import hashlib
import json


# -------------------------
# Canonical Enums (v0)
# -------------------------

DRIFT_CLASSES = {"none", "benign", "structural", "critical"}


# -------------------------
# Helpers
# -------------------------

def _stable_json(data: Dict[str, Any]) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _hash_payload(payload: Dict[str, Any]) -> str:
    stable = _stable_json(payload)
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


# -------------------------
# IR Definitions
# -------------------------

@dataclass(frozen=True)
class WardFlag:
    """
    WardFlag.v0

    A single governance signal. Always additive (never destructive).
    """

    code: str               # stable identifier, e.g., "TIER_LEAKAGE"
    message: str            # short human-readable summary
    severity: str           # e.g., "info"|"warn"|"error" (string to avoid enum coupling)
    meta: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.code:
            raise ValueError("WardFlag.code must be non-empty")
        if not self.message:
            raise ValueError("WardFlag.message must be non-empty")
        if not self.severity:
            raise ValueError("WardFlag.severity must be non-empty")
        if not isinstance(self.meta, dict):
            raise ValueError("WardFlag.meta must be a dict")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "meta": self.meta,
        }


@dataclass(frozen=True)
class WardReport:
    """
    WardReport.v0

    Top-level governance report.
    """

    report_id: str

    violations: List[WardFlag] = field(default_factory=list)
    warnings: List[WardFlag] = field(default_factory=list)

    tier_leakage_flags: List[str] = field(default_factory=list)

    drift_class: str = "none"     # none | benign | structural | critical
    invariance_passed: Optional[bool] = None  # None when invariance not executed

    not_computable: bool = False
    missing_fields: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.drift_class not in DRIFT_CLASSES:
            raise ValueError(f"Invalid drift_class: {self.drift_class}")

        for f in self.violations:
            if not isinstance(f, WardFlag):
                raise ValueError("violations must contain WardFlag objects")
            f.validate()

        for f in self.warnings:
            if not isinstance(f, WardFlag):
                raise ValueError("warnings must contain WardFlag objects")
            f.validate()

        if not isinstance(self.tier_leakage_flags, list):
            raise ValueError("tier_leakage_flags must be a list")

        if self.not_computable and not self.missing_fields:
            raise ValueError("not_computable=True requires missing_fields to be non-empty")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "violations": [v.to_payload() for v in self.violations],
            "warnings": [w.to_payload() for w in self.warnings],
            "tier_leakage_flags": list(self.tier_leakage_flags),
            "drift_class": self.drift_class,
            "invariance_passed": self.invariance_passed,
            "not_computable": self.not_computable,
            "missing_fields": list(self.missing_fields),
        }

    def hash(self) -> str:
        self.validate()
        return _hash_payload(self.to_payload())

    def semantically_equal(self, other: "WardReport") -> bool:
        if not isinstance(other, WardReport):
            return False
        return self.hash() == other.hash()
