from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from abraxas.core.provenance import hash_canonical_json
from server.abraxas.upgrade_spine.types import UpgradeCandidate
from server.abraxas.upgrade_spine.utils import (
    compute_candidate_id,
    not_computable_payload,
    build_patch_plan,
    read_jsonl,
    stable_input_hash,
    utc_now_iso,
)


def _summarize_shadow(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not entries:
        return {"shadow_metrics": {}, "entries": 0}
    latest = entries[-1]
    return {
        "entries": len(entries),
        "latest_cycle": latest.get("cycle"),
        "shadow_metrics": latest.get("shadow_metrics", {}),
    }


def collect_shadow_candidates(base_path: Path) -> List[UpgradeCandidate]:
    ledger_path = base_path / ".aal" / "ledger" / "outcomes.jsonl"
    if not ledger_path.exists():
        missing = not_computable_payload(
            reason="missing_shadow_outcomes_ledger",
            missing_inputs=[str(ledger_path)],
            provenance={"base_path": str(base_path)},
        )
        payload = {
            "source_loop": "shadow",
            "change_type": "thresholds",
            "target_paths": [],
            "patch_plan": build_patch_plan(
                operations=[{"op": "collect_shadow_outcomes", "ledger_path": str(ledger_path)}],
                notes=["shadow_missing"],
            ),
            "evidence_refs": [],
            "constraints": {"shadow_only": True},
            "not_computable": missing,
        }
        candidate_id = compute_candidate_id(payload)
        return [
            UpgradeCandidate(
                version="upgrade_candidate.v0",
                run_id="shadow",
                created_at=utc_now_iso(),
                input_hash=stable_input_hash(payload),
                candidate_id=candidate_id,
                source_loop="shadow",
                change_type="thresholds",
                target_paths=[],
                patch_plan=payload["patch_plan"],
                evidence_refs=[],
                constraints=payload["constraints"],
                not_computable=missing,
            )
        ]

    entries = read_jsonl(ledger_path)
    summary = _summarize_shadow(entries)
    evidence_refs = [str(ledger_path)]
    patch_plan = build_patch_plan(
        operations=[
            {
                "op": "review_shadow_summary",
                "entries": summary.get("entries", 0),
                "latest_cycle": summary.get("latest_cycle"),
                "shadow_metrics": summary.get("shadow_metrics", {}),
            }
        ],
        notes=["shadow_summary_reference"],
        metadata={"evidence_count": len(evidence_refs)},
    )
    candidate_payload = {
        "source_loop": "shadow",
        "change_type": "thresholds",
        "target_paths": [],
        "patch_plan": patch_plan,
        "evidence_refs": evidence_refs,
        "constraints": {"shadow_only": True},
        "not_computable": not_computable_payload(
            reason="shadow_observation_only",
            missing_inputs=[],
            provenance={"summary": summary},
        ),
    }
    candidate_id = compute_candidate_id(candidate_payload)
    return [
        UpgradeCandidate(
            version="upgrade_candidate.v0",
            run_id="shadow",
            created_at=utc_now_iso(),
            input_hash=hash_canonical_json(summary),
            candidate_id=candidate_id,
            source_loop="shadow",
            change_type="thresholds",
            target_paths=[],
            patch_plan=patch_plan,
            evidence_refs=evidence_refs,
            constraints={"shadow_only": True},
            not_computable=candidate_payload["not_computable"],
        )
    ]
