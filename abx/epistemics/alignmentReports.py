from __future__ import annotations

from abx.epistemics.alignmentInventory import build_alignment_inventory
from abx.epistemics.groundTruthReferences import build_ground_truth_references
from abx.epistemics.replayComparisons import build_replay_comparisons
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def classify_alignment_modes() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {
        "direct_ground_truth_alignment": [],
        "proxy_reference_alignment": [],
        "replay_consistency_only": [],
        "heuristic_alignment": [],
        "not_computable": [],
    }
    for row in build_alignment_inventory():
        out[row.alignment_class].append(row.alignment_id)
    return {k: sorted(v) for k, v in out.items()}


def classify_alignment_mismatches() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"none": [], "within_tolerance": [], "semantic_drift": [], "unknown": []}
    for row in build_replay_comparisons():
        key = row.mismatch_class if row.mismatch_class in out else "unknown"
        out[key].append(row.comparison_id)
    return {k: sorted(v) for k, v in out.items()}


def build_alignment_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "AlignmentAudit.v1",
        "artifactId": "alignment-audit",
        "alignmentRecords": [x.__dict__ for x in build_alignment_inventory()],
        "groundTruthReferences": [x.__dict__ for x in build_ground_truth_references()],
        "replayComparisons": [x.__dict__ for x in build_replay_comparisons()],
        "alignmentModes": classify_alignment_modes(),
        "mismatchClassification": classify_alignment_mismatches(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
