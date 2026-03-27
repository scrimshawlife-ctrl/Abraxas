from __future__ import annotations

from abx.productization.outputBoundedness import build_output_boundedness_records
from abx.productization.outputInterpretability import build_output_interpretability_records
from abx.productization.packageTiers import build_package_tiers
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def classify_output_boundedness() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {
        "safe_complete_for_audience": [],
        "bounded_limited": [],
        "degraded_but_usable": [],
        "caution_required": [],
        "not_suitable": [],
        "not_computable": [],
    }
    for row in build_output_boundedness_records():
        out[row.boundedness_state].append(row.boundedness_id)
    return {k: sorted(v) for k, v in out.items()}


def build_output_boundedness_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "OutputBoundednessAudit.v1",
        "artifactId": "output-boundedness-audit",
        "boundedness": [x.__dict__ for x in build_output_boundedness_records()],
        "interpretability": [x.__dict__ for x in build_output_interpretability_records()],
        "packageTiers": [x.__dict__ for x in build_package_tiers()],
        "boundednessClassification": classify_output_boundedness(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
