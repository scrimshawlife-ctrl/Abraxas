#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Literal


OrderCategory = Literal["hard_blockers", "prerequisite_patches", "downstream_patches", "optional_cleanup"]


AXIS_TO_PATCH = {
    "proof_chain_continuity_emit_ledger_validate": {
        "patch_id": "PATCH.CLOSURE.001",
        "title": "Map probe runs to deterministic ledger records for validator continuity",
        "target_surfaces": [
            "abx/execution_validator.py",
            "out/ledger/*.jsonl (run-linked ingestion source)",
            "aal_core/runes/compliance_probe.py",
        ],
        "expected_closure_impact": "Unblocks continuity by populating validator correlation.ledgerIds for probe runs.",
        "dependencies": [],
    },
    "correlation_pointer_sufficiency": {
        "patch_id": "PATCH.CLOSURE.002",
        "title": "Promote non-empty correlation pointers from resolved evidence into probe continuity path",
        "target_surfaces": [
            "aal_core/runes/compliance_probe.py",
            "abx/execution_validator.py",
        ],
        "expected_closure_impact": "Raises pointer sufficiency from structural presence to proof-meaningful linkage.",
        "dependencies": ["PATCH.CLOSURE.001"],
    },
    "promotion_relevant_evidence_sufficiency": {
        "patch_id": "PATCH.CLOSURE.003",
        "title": "Add promotion-readiness gate based on continuity + pointer sufficiency evidence",
        "target_surfaces": [
            "scripts/run_closure_readiness_audit.py",
            "artifacts_seal/audits/closure_readiness/*",
            "PLANS.md",
        ],
        "expected_closure_impact": "Moves promotion evidence from partial to closure-grade auditable criteria.",
        "dependencies": ["PATCH.CLOSURE.001", "PATCH.CLOSURE.002"],
    },
    "validator_visible_surfacing": {
        "patch_id": "PATCH.CLOSURE.004",
        "title": "Expand validator surfacing coverage across probe runs",
        "target_surfaces": [
            "aal_core/runes/compliance_probe.py",
            "out/validators/execution-validation-*.json",
        ],
        "expected_closure_impact": "Improves breadth of surfaced runs without blocking continuity closure.",
        "dependencies": [],
    },
    "run_linked_artifact_visibility": {
        "patch_id": "PATCH.CLOSURE.005",
        "title": "Harden run-linked artifact visibility checks",
        "target_surfaces": [
            "scripts/run_closure_readiness_audit.py",
            "artifacts_seal/runs/compliance_probe/*.artifact.json",
        ],
        "expected_closure_impact": "Non-blocking assurance hardening for already satisfied visibility.",
        "dependencies": [],
    },
    "linkage_preservation": {
        "patch_id": "PATCH.CLOSURE.006",
        "title": "Harden linkage field contract checks",
        "target_surfaces": [
            "scripts/run_closure_readiness_audit.py",
            "aal_core/schemas/rune_execution_artifact.v1.json",
        ],
        "expected_closure_impact": "Non-blocking assurance hardening for already satisfied linkage preservation.",
        "dependencies": [],
    },
}


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected dict JSON at {path}")
    return payload


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _category_for_status(axis: str, status: str) -> OrderCategory:
    if status == "BLOCKED":
        return "hard_blockers"
    if status == "MISSING":
        return "prerequisite_patches"
    if status == "PARTIAL":
        if axis in {"correlation_pointer_sufficiency", "promotion_relevant_evidence_sufficiency"}:
            return "downstream_patches"
        return "prerequisite_patches"
    return "optional_cleanup"


def _patch_for_axis(axis: str, status: str) -> Dict[str, Any]:
    patch = dict(AXIS_TO_PATCH[axis])
    patch["axis"] = axis
    patch["source_status"] = status
    return patch


def build_ordering_artifact(*, audit_path: Path) -> Dict[str, Any]:
    raw = audit_path.read_text(encoding="utf-8")
    audit = _load_json(audit_path)
    classifications = audit.get("classifications", {})
    if not isinstance(classifications, dict):
        raise ValueError("Audit artifact missing dict classifications")

    ordered_axes = sorted(classifications.keys())
    category_buckets: Dict[OrderCategory, List[Dict[str, Any]]] = {
        "hard_blockers": [],
        "prerequisite_patches": [],
        "downstream_patches": [],
        "optional_cleanup": [],
    }
    dependency_notes: List[str] = []

    for axis in ordered_axes:
        status_node = classifications.get(axis, {})
        status = str(status_node.get("status", "MISSING"))
        if axis not in AXIS_TO_PATCH:
            continue
        patch = _patch_for_axis(axis, status)
        category = _category_for_status(axis, status)
        category_buckets[category].append(patch)
        for dep in patch.get("dependencies", []):
            dependency_notes.append(f"{patch['patch_id']} depends on {dep}")

    for bucket in category_buckets.values():
        bucket.sort(key=lambda item: item["patch_id"])

    ordered_patch_list = (
        category_buckets["hard_blockers"]
        + category_buckets["prerequisite_patches"]
        + category_buckets["downstream_patches"]
        + category_buckets["optional_cleanup"]
    )
    recommended_first_patch = ordered_patch_list[0]["patch_id"] if ordered_patch_list else "NOT_COMPUTABLE"

    return {
        "schema_version": "aal.closure_remediation_order.v1",
        "audit_input": {
            "path": audit_path.as_posix(),
            "sha256": _sha256_text(raw),
            "schema_version": audit.get("schema_version", ""),
        },
        "ordering_categories": category_buckets,
        "ordered_patch_list": [item["patch_id"] for item in ordered_patch_list],
        "dependency_notes": sorted(set(dependency_notes)),
        "recommended_first_patch": recommended_first_patch,
        "recommendation_reason": "Earliest blocker/prerequisite by deterministic category-first order.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Derive deterministic closure remediation order from closure readiness audit.")
    parser.add_argument(
        "--audit",
        default="artifacts_seal/audits/closure_readiness/closure_readiness.audit.v1.json",
        help="Path to closure readiness audit artifact.",
    )
    parser.add_argument(
        "--out",
        default="artifacts_seal/audits/closure_readiness/closure_remediation_order.v1.json",
        help="Output path for remediation ordering artifact.",
    )
    args = parser.parse_args()

    audit_path = Path(args.audit)
    artifact = build_ordering_artifact(audit_path=audit_path)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
