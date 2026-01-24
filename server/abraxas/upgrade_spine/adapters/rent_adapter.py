from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from abraxas.core.provenance import hash_canonical_json
from server.abraxas.upgrade_spine.types import UpgradeCandidate
from server.abraxas.upgrade_spine.utils import (
    compute_candidate_id,
    not_computable_payload,
    patch_plan_stub,
    pick_paths,
    read_json,
    stable_input_hash,
    utc_now_iso,
)


def _load_latest_report(report_paths: List[Path]) -> Path:
    return sorted(report_paths)[-1]


def collect_rent_candidates(base_path: Path) -> List[UpgradeCandidate]:
    report_paths = pick_paths(base_path / "out" / "reports", "rent_check_*.json")
    if not report_paths:
        missing = not_computable_payload(
            reason="missing_rent_reports",
            missing_inputs=["out/reports/rent_check_*.json"],
            provenance={"base_path": str(base_path)},
        )
        payload = {
            "source_loop": "rent",
            "change_type": "rules",
            "target_paths": ["data/rent_manifests"],
            "patch_plan": patch_plan_stub(notes=["rent_missing"]),
            "evidence_refs": [],
            "constraints": {"rent_gate_required": True},
            "not_computable": missing,
        }
        candidate_id = compute_candidate_id(payload)
        return [
            UpgradeCandidate(
                version="upgrade_candidate.v0",
                run_id="rent",
                created_at=utc_now_iso(),
                input_hash=stable_input_hash(payload),
                candidate_id=candidate_id,
                source_loop="rent",
                change_type="rules",
                target_paths=payload["target_paths"],
                patch_plan=payload["patch_plan"],
                evidence_refs=[],
                constraints=payload["constraints"],
                not_computable=missing,
            )
        ]

    report_path = _load_latest_report(report_paths)
    report = read_json(report_path)
    failures = report.get("failures", [])
    warnings = report.get("warnings", [])
    issues = failures + warnings
    not_computable = None
    if not issues:
        not_computable = not_computable_payload(
            reason="rent_gate_green",
            missing_inputs=[],
            provenance={"report": str(report_path)},
        )
    patch_plan = patch_plan_stub(notes=["rent_report_reference"])
    candidate_payload = {
        "source_loop": "rent",
        "change_type": "rules",
        "target_paths": ["data/rent_manifests"],
        "patch_plan": patch_plan,
        "evidence_refs": [str(report_path)],
        "constraints": {"rent_gate_required": True},
        "not_computable": not_computable,
    }
    candidate_id = compute_candidate_id(candidate_payload)
    return [
        UpgradeCandidate(
            version="upgrade_candidate.v0",
            run_id="rent",
            created_at=utc_now_iso(),
            input_hash=hash_canonical_json(report),
            candidate_id=candidate_id,
            source_loop="rent",
            change_type="rules",
            target_paths=["data/rent_manifests"],
            patch_plan=patch_plan,
            evidence_refs=[str(report_path)],
            constraints={"rent_gate_required": True},
            not_computable=not_computable,
        )
    ]
