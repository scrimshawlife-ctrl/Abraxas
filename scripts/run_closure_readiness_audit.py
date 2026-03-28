#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Literal


AuditStatus = Literal["SATISFIED", "PARTIAL", "MISSING", "BLOCKED"]


def _load_json(path: Path) -> Dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _collect(paths: Iterable[Path]) -> list[tuple[Path, Dict[str, Any]]]:
    out: list[tuple[Path, Dict[str, Any]]] = []
    for path in sorted(paths):
        payload = _load_json(path)
        if payload is not None:
            out.append((path, payload))
    return out


def _audit_status_block(
    *,
    status: AuditStatus,
    reason: str,
    evidence: list[str],
    next_patch_hint: str,
) -> Dict[str, Any]:
    return {
        "status": status,
        "reason": reason,
        "evidence": sorted(set(evidence)),
        "next_patch_hint": next_patch_hint,
    }


def _promotion_gate_evidence(
    *,
    continuity: Dict[str, Any],
    pointer_sufficiency: Dict[str, Any],
    visibility: Dict[str, Any],
    linkage_preservation: Dict[str, Any],
    validator_surfacing: Dict[str, Any],
) -> tuple[AuditStatus, str, list[str]]:
    """Classify promotion-readiness using explicit closure-grade gate criteria.

    PATCH.CLOSURE.003 requires this gate to be evidence-backed and deterministic.
    """

    required_axes = {
        "continuity": continuity,
        "pointer_sufficiency": pointer_sufficiency,
    }
    supporting_axes = {
        "visibility": visibility,
        "linkage": linkage_preservation,
        "surfacing": validator_surfacing,
    }

    required_sat = all(block.get("status") == "SATISFIED" for block in required_axes.values())
    supporting_sat = all(block.get("status") == "SATISFIED" for block in supporting_axes.values())

    evidence = [
        f"gate.required.{name}:{block.get('status', 'MISSING')}" for name, block in required_axes.items()
    ] + [
        f"gate.supporting.{name}:{block.get('status', 'MISSING')}" for name, block in supporting_axes.items()
    ]

    if required_sat and supporting_sat:
        return (
            "SATISFIED",
            "Promotion-readiness gate passed with closure-grade continuity + pointer sufficiency and supporting proof visibility.",
            evidence,
        )
    if required_sat and not supporting_sat:
        return (
            "PARTIAL",
            "Promotion-readiness gate has closure-critical continuity + pointer sufficiency, but supporting visibility/linkage/surfacing remains incomplete.",
            evidence,
        )
    if any(block.get("status") in {"PARTIAL", "BLOCKED"} for block in required_axes.values()):
        return (
            "BLOCKED",
            "Promotion-readiness gate blocked: continuity and pointer sufficiency must both be SATISFIED.",
            evidence,
        )
    return (
        "MISSING",
        "Promotion-readiness gate missing required closure evidence for continuity and pointer sufficiency.",
        evidence,
    )


def build_closure_readiness_audit(*, base_dir: Path) -> Dict[str, Any]:
    compliance_artifacts = _collect((base_dir / "artifacts_seal/runs/compliance_probe").glob("*.artifact.json"))
    validator_surface = _collect(
        (base_dir / "artifacts_seal/runs/compliance_probe").glob("*.validator_surface_probe.json")
    )
    validator_outputs = _collect((base_dir / "out/validators").glob("execution-validation-*.json"))

    by_run_compliance = {str(payload.get("run_id", "")): (path, payload) for path, payload in compliance_artifacts}
    by_run_surface = {str(payload.get("run_id", "")): (path, payload) for path, payload in validator_surface}
    by_run_validator = {str(payload.get("runId", "")): (path, payload) for path, payload in validator_outputs}
    intersect_runs = sorted(set(by_run_compliance) & set(by_run_surface) & set(by_run_validator) - {""})

    visibility_evidence = [
        f"{path.as_posix()}#{payload.get('run_id')}:{payload.get('artifact_id')}"
        for path, payload in compliance_artifacts
        if payload.get("run_id") and payload.get("artifact_id")
    ]
    visibility = _audit_status_block(
        status="SATISFIED" if visibility_evidence else "MISSING",
        reason="Run-linked compliance artifacts are emitted with run_id/artifact_id."
        if visibility_evidence
        else "No run-linked compliance artifacts found.",
        evidence=visibility_evidence[:20],
        next_patch_hint="Ensure probe emission is executed before closure audit."
        if not visibility_evidence
        else "Maintain deterministic artifact emission contract.",
    )

    linkage_evidence: list[str] = []
    missing_linkage_fields: list[str] = []
    for path, payload in compliance_artifacts:
        for key in ("ledger_record_ids", "ledger_artifact_ids", "correlation_pointers"):
            if key not in payload:
                missing_linkage_fields.append(f"{path.as_posix()} missing {key}")
        if all(key in payload for key in ("ledger_record_ids", "ledger_artifact_ids", "correlation_pointers")):
            linkage_evidence.append(path.as_posix())
    linkage_preservation = _audit_status_block(
        status="SATISFIED" if linkage_evidence and not missing_linkage_fields else "MISSING",
        reason="Linkage fields are structurally preserved on emitted compliance artifacts."
        if linkage_evidence and not missing_linkage_fields
        else "One or more compliance artifacts missing required linkage fields.",
        evidence=(linkage_evidence[:20] + missing_linkage_fields[:20]),
        next_patch_hint="Normalize missing linkage fields at emission boundary.",
    )

    surface_statuses = [str(payload.get("validator_surface_status", "")) for _, payload in validator_surface]
    surfaced_evidence = [
        path.as_posix()
        for path, payload in validator_surface
        if payload.get("validator_surface_status") == "SURFACED_TO_VALIDATOR_OUTPUT"
    ]
    validator_surfacing = _audit_status_block(
        status="SATISFIED"
        if surfaced_evidence
        else ("PARTIAL" if surface_statuses else "MISSING"),
        reason="At least one probe run is surfaced to validator-visible output."
        if surfaced_evidence
        else (
            "Validator-surface artifacts exist but none are surfaced."
            if surface_statuses
            else "No validator-surface probe artifacts found."
        ),
        evidence=surfaced_evidence[:20],
        next_patch_hint="Investigate validator path matching and probe run-id alignment."
        if not surfaced_evidence
        else "Expand surfaced coverage across proof runs.",
    )

    pointer_rich_runs = []
    for run_id in intersect_runs:
        _, compliance_payload = by_run_compliance[run_id]
        if compliance_payload.get("correlation_pointers"):
            pointer_rich_runs.append(run_id)
    pointer_sufficiency = _audit_status_block(
        status="SATISFIED"
        if pointer_rich_runs
        else ("PARTIAL" if intersect_runs else "MISSING"),
        reason="Correlation pointers are present for at least one run across compliance/validator surfaces."
        if pointer_rich_runs
        else (
            "Correlation pointers are structurally present but empty on intersected proof runs."
            if intersect_runs
            else "No intersected proof runs found across compliance/surface/validator outputs."
        ),
        evidence=pointer_rich_runs[:20],
        next_patch_hint="Propagate non-empty correlation pointers from ledger/validator evidence into compliance runs.",
    )

    continuity_runs: list[str] = []
    blocked_runs: list[str] = []
    for run_id in intersect_runs:
        _, validator_payload = by_run_validator[run_id]
        validated_artifacts = validator_payload.get("validatedArtifacts", [])
        ledger_ids = validator_payload.get("correlation", {}).get("ledgerIds", [])
        if validated_artifacts and ledger_ids:
            continuity_runs.append(run_id)
        else:
            blocked_runs.append(run_id)
    continuity = _audit_status_block(
        status="SATISFIED"
        if continuity_runs
        else ("BLOCKED" if blocked_runs else "MISSING"),
        reason="Emit→ledger→validate continuity proven for at least one run."
        if continuity_runs
        else (
            "Runs reach validator output but ledger linkage leg is empty or missing."
            if blocked_runs
            else "No intersected runs available to test continuity."
        ),
        evidence=(continuity_runs[:20] + blocked_runs[:20]),
        next_patch_hint="Add or map run-linked ledger records for probe runs so validator correlation.ledgerIds is populated.",
    )

    promotion_status, promotion_reason, promotion_evidence = _promotion_gate_evidence(
        continuity=continuity,
        pointer_sufficiency=pointer_sufficiency,
        visibility=visibility,
        linkage_preservation=linkage_preservation,
        validator_surfacing=validator_surfacing,
    )
    promotion = _audit_status_block(
        status=promotion_status,
        reason=promotion_reason,
        evidence=promotion_evidence,
        next_patch_hint="Close continuity and pointer sufficiency gaps before closure-grade promotion claims.",
    )

    return {
        "schema_version": "aal.closure_readiness.audit.v1",
        "audit_scope": "compliance_probe + execution_validator proof-chain surfaces",
        "inspected": {
            "compliance_artifacts": len(compliance_artifacts),
            "validator_surface_artifacts": len(validator_surface),
            "validator_outputs": len(validator_outputs),
            "intersected_runs": len(intersect_runs),
        },
        "classifications": {
            "run_linked_artifact_visibility": visibility,
            "linkage_preservation": linkage_preservation,
            "validator_visible_surfacing": validator_surfacing,
            "correlation_pointer_sufficiency": pointer_sufficiency,
            "proof_chain_continuity_emit_ledger_validate": continuity,
            "promotion_relevant_evidence_sufficiency": promotion,
        },
        "remediation_queue": [
            item["next_patch_hint"]
            for item in (
                visibility,
                linkage_preservation,
                validator_surfacing,
                pointer_sufficiency,
                continuity,
                promotion,
            )
            if item["status"] in {"PARTIAL", "MISSING", "BLOCKED"}
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify closure-grade readiness for compliance/validator proof-chain surfaces.")
    parser.add_argument("--base-dir", default=".", help="Repository base directory.")
    parser.add_argument(
        "--out",
        default="artifacts_seal/audits/closure_readiness/closure_readiness.audit.v1.json",
        help="Output path for deterministic closure readiness artifact.",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    artifact = build_closure_readiness_audit(base_dir=base_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
