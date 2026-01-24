from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from abraxas.core.provenance import hash_canonical_json
from server.abraxas.upgrade_spine.types import UpgradeCandidate
from server.abraxas.upgrade_spine.utils import (
    compute_candidate_id,
    not_computable_payload,
    patch_plan_stub,
    read_json,
    stable_input_hash,
    utc_now_iso,
)


def collect_drift_candidates(base_path: Path) -> List[UpgradeCandidate]:
    drift_path = base_path / "out" / "drift_report_v1.json"
    if not drift_path.exists():
        missing = not_computable_payload(
            reason="missing_drift_report",
            missing_inputs=[str(drift_path)],
            provenance={"base_path": str(base_path)},
        )
        payload = {
            "source_loop": "drift",
            "change_type": "thresholds",
            "target_paths": [],
            "patch_plan": patch_plan_stub(notes=["drift_missing"]),
            "evidence_refs": [],
            "constraints": {"drift_gate_required": True},
            "not_computable": missing,
        }
        candidate_id = compute_candidate_id(payload)
        return [
            UpgradeCandidate(
                version="upgrade_candidate.v0",
                run_id="drift",
                created_at=utc_now_iso(),
                input_hash=stable_input_hash(payload),
                candidate_id=candidate_id,
                source_loop="drift",
                change_type="thresholds",
                target_paths=[],
                patch_plan=payload["patch_plan"],
                evidence_refs=[],
                constraints=payload["constraints"],
                not_computable=missing,
            )
        ]

    report = read_json(drift_path)
    patch_plan = patch_plan_stub(notes=["drift_report_reference"])
    candidate_payload = {
        "source_loop": "drift",
        "change_type": "thresholds",
        "target_paths": [],
        "patch_plan": patch_plan,
        "evidence_refs": [str(drift_path)],
        "constraints": {"drift_gate_required": True},
        "not_computable": not_computable_payload(
            reason="drift_summary_observation_only",
            missing_inputs=[],
            provenance={"schema_version": report.get("schema_version")},
        ),
    }
    candidate_id = compute_candidate_id(candidate_payload)
    return [
        UpgradeCandidate(
            version="upgrade_candidate.v0",
            run_id="drift",
            created_at=utc_now_iso(),
            input_hash=hash_canonical_json(report),
            candidate_id=candidate_id,
            source_loop="drift",
            change_type="thresholds",
            target_paths=[],
            patch_plan=patch_plan,
            evidence_refs=[str(drift_path)],
            constraints={"drift_gate_required": True},
            not_computable=candidate_payload["not_computable"],
        )
    ]
