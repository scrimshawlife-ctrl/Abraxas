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


def _candidate_from_evogate(path: Path, payload: Dict[str, Any]) -> UpgradeCandidate:
    run_id = str(payload.get("run_id") or payload.get("pack_id") or "evogate")
    created_at = str(payload.get("ts") or utc_now_iso())
    evidence_refs = [str(path)]
    patch_plan = patch_plan_stub(
        notes=["evogate_candidate_policy_reference"]
    )
    candidate_payload = {
        "source_loop": "evogate",
        "change_type": "rules",
        "target_paths": [str(payload.get("candidate_policy_path", ""))],
        "patch_plan": patch_plan,
        "evidence_refs": evidence_refs,
        "constraints": {"no_direct_canon_write": True},
        "not_computable": not_computable_payload(
            reason="candidate_policy_mapping_not_defined",
            missing_inputs=[],
            provenance={"evogate_path": str(path)},
        ),
    }
    candidate_id = compute_candidate_id(candidate_payload)
    return UpgradeCandidate(
        version="upgrade_candidate.v0",
        run_id=run_id,
        created_at=created_at,
        input_hash=stable_input_hash(payload, {"path": str(path)}),
        candidate_id=candidate_id,
        source_loop="evogate",
        change_type="rules",
        target_paths=[str(payload.get("candidate_policy_path", ""))],
        patch_plan=patch_plan,
        evidence_refs=evidence_refs,
        constraints={"no_direct_canon_write": True},
        not_computable=candidate_payload["not_computable"],
    )


def _candidate_from_evolution(path: Path, payload: Dict[str, Any]) -> UpgradeCandidate:
    run_id = str(payload.get("candidate_id") or "evolution")
    created_at = str(payload.get("proposed_at") or utc_now_iso())
    kind = str(payload.get("kind", "param_tweak")).lower()
    change_type = "thresholds" if kind == "param_tweak" else "module_additive"
    target_paths = ["data/evolution/param_overrides.yaml"]
    patch_plan = {
        "format_version": "0.1",
        "operations": [
            {
                "op": "param_override",
                "param_path": payload.get("param_path"),
                "value": payload.get("proposed_value"),
                "previous_value": payload.get("current_value"),
                "candidate_id": payload.get("candidate_id"),
                "rationale": payload.get("rationale"),
            }
        ],
        "notes": ["evolution_param_override_v0_1"],
    }
    constraints = {"no_direct_canon_write": True}
    not_computable = None
    if kind != "param_tweak":
        patch_plan = patch_plan_stub(notes=["evolution_candidate_ticket_required"])
        constraints["requires_implementation_ticket"] = True
        target_paths = ["data/evolution/implementation_tickets"]
        not_computable = not_computable_payload(
            reason="implementation_ticket_required",
            missing_inputs=[],
            provenance={"candidate_kind": kind},
        )
    candidate_payload = {
        "source_loop": "evogate",
        "change_type": change_type,
        "target_paths": target_paths,
        "patch_plan": patch_plan,
        "evidence_refs": [str(path)],
        "constraints": constraints,
        "not_computable": not_computable,
    }
    candidate_id = compute_candidate_id(candidate_payload)
    return UpgradeCandidate(
        version="upgrade_candidate.v0",
        run_id=run_id,
        created_at=created_at,
        input_hash=hash_canonical_json(payload),
        candidate_id=candidate_id,
        source_loop="evogate",
        change_type=change_type,
        target_paths=target_paths,
        patch_plan=patch_plan,
        evidence_refs=[str(path)],
        constraints=constraints,
        not_computable=not_computable,
    )


def collect_evogate_candidates(base_path: Path) -> List[UpgradeCandidate]:
    candidates: List[UpgradeCandidate] = []
    evogate_paths = pick_paths(base_path / "out", "evogate_*.json")
    if not evogate_paths:
        missing = not_computable_payload(
            reason="missing_evogate_reports",
            missing_inputs=["out/**/evogate_*.json"],
            provenance={"base_path": str(base_path)},
        )
        payload = {
            "source_loop": "evogate",
            "change_type": "rules",
            "target_paths": [],
            "patch_plan": patch_plan_stub(notes=["evogate_missing"]),
            "evidence_refs": [],
            "constraints": {"no_direct_canon_write": True},
            "not_computable": missing,
        }
        candidate_id = compute_candidate_id(payload)
        candidates.append(
            UpgradeCandidate(
                version="upgrade_candidate.v0",
                run_id="evogate",
                created_at=utc_now_iso(),
                input_hash=stable_input_hash(payload),
                candidate_id=candidate_id,
                source_loop="evogate",
                change_type="rules",
                target_paths=[],
                patch_plan=payload["patch_plan"],
                evidence_refs=[],
                constraints=payload["constraints"],
                not_computable=missing,
            )
        )
        return candidates

    for path in evogate_paths:
        payload = read_json(path)
        candidates.append(_candidate_from_evogate(path, payload))

    evolution_paths = pick_paths(base_path / "data" / "evolution" / "candidates", "*.json")
    for path in evolution_paths:
        payload = read_json(path)
        candidates.append(_candidate_from_evolution(path, payload))

    return candidates
