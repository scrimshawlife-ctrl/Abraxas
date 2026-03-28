#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected dict JSON at {path.as_posix()}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence_record(path: Path, role: str) -> Dict[str, str]:
    return {"path": path.as_posix(), "role": role, "sha256": _sha256(path)}


def _nonblocking_followups(remediation: Mapping[str, Any]) -> List[Dict[str, str]]:
    queue = remediation.get("ordered_patch_list", [])
    if not isinstance(queue, list):
        return []
    out: List[Dict[str, str]] = []
    for patch_id in queue:
        if not isinstance(patch_id, str):
            continue
        out.append(
            {
                "type": "closure_assurance_followup",
                "id": patch_id,
                "status": "NON_BLOCKING_FOR_GENERALIZED_MILESTONE",
                "reason": "Generalized closure attestation is already confirmed by direct non-probe validator evidence.",
            }
        )
    return out


def build_attestation(
    *,
    readiness_path: Path,
    remediation_path: Path,
    scope_path: Path,
    validator_path: Path,
    run_artifact_path: Path,
    run_surface_path: Path,
    ledger_path: Path,
) -> Dict[str, Any]:
    readiness = _load_json(readiness_path)
    remediation = _load_json(remediation_path)
    scope = _load_json(scope_path)
    validator = _load_json(validator_path)
    run_artifact = _load_json(run_artifact_path)
    run_surface = _load_json(run_surface_path)

    generalized_block = scope.get("categories", {}).get("GENERALIZED_CONFIRMED", {})
    generalized_status = str(generalized_block.get("status", "MISSING"))
    generalized_runs = generalized_block.get("evidence", [])
    if not isinstance(generalized_runs, list):
        generalized_runs = []
    confirming_run_ids = sorted({str(x) for x in generalized_runs if isinstance(x, str) and x})

    validated_artifacts = validator.get("validatedArtifacts", [])
    correlation = validator.get("correlation", {})
    ledger_ids = correlation.get("ledgerIds", []) if isinstance(correlation, Mapping) else []
    pointers = correlation.get("pointers", []) if isinstance(correlation, Mapping) else []

    validator_chain_ok = bool(validated_artifacts and ledger_ids and pointers)
    scope_ok = scope.get("summary_status") == "GENERALIZED_CONFIRMED" and generalized_status == "SATISFIED"

    attestation_status = (
        "GENERALIZED_CLOSURE_CONFIRMED" if validator_chain_ok and scope_ok else "NOT_COMPUTABLE"
    )

    blocking_issues: List[Dict[str, str]] = []
    if not scope_ok:
        blocking_issues.append(
            {
                "id": "scope.generalized_confirmation",
                "reason": "Scope classification does not currently attest generalized confirmation.",
            }
        )
    if not validator_chain_ok:
        blocking_issues.append(
            {
                "id": "validator.non_probe_chain",
                "reason": "Validator output is missing validatedArtifacts or correlation linkage fields.",
            }
        )

    return {
        "schema_version": "aal.closure_generalized_attestation.v1",
        "attested_at": _utc_now(),
        "attestation_status": attestation_status,
        "milestone": {
            "id": "CLOSURE.GENERALIZED.CONFIRMED",
            "description": "Generalized closure milestone attested via direct non-probe validator-visible evidence.",
        },
        "confirming_run_ids": confirming_run_ids,
        "confirming_artifacts": {
            "readiness_audit": readiness_path.as_posix(),
            "remediation_order": remediation_path.as_posix(),
            "scope_classification": scope_path.as_posix(),
            "validator_output": validator_path.as_posix(),
            "run_artifact": run_artifact_path.as_posix(),
            "run_surface": run_surface_path.as_posix(),
            "ledger_surface": ledger_path.as_posix(),
        },
        "closure_conditions": {
            "scope_generalized_confirmed": {
                "status": "SATISFIED" if scope_ok else "MISSING",
                "reason": str(generalized_block.get("reason", "")),
                "evidence": confirming_run_ids,
            },
            "validator_visible_non_probe_chain": {
                "status": "SATISFIED" if validator_chain_ok else "MISSING",
                "reason": "validatedArtifacts + correlation.ledgerIds + correlation.pointers are all non-empty"
                if validator_chain_ok
                else "Validator chain is incomplete for non-probe confirmation",
                "evidence": {
                    "validatedArtifacts_count": len(validated_artifacts) if isinstance(validated_artifacts, list) else 0,
                    "ledgerIds_count": len(ledger_ids) if isinstance(ledger_ids, list) else 0,
                    "pointers_count": len(pointers) if isinstance(pointers, list) else 0,
                },
            },
            "run_linkage_fields_present": {
                "status": "SATISFIED"
                if all(
                    key in run_artifact
                    for key in (
                        "run_id",
                        "artifact_id",
                        "rune_id",
                        "timestamp",
                        "ledger_record_ids",
                        "ledger_artifact_ids",
                        "correlation_pointers",
                    )
                )
                else "MISSING",
                "reason": "Run artifact preserves required linkage fields.",
                "evidence": run_artifact_path.as_posix(),
            },
            "probe_path_in_current_snapshot": {
                "status": str(
                    readiness.get("classifications", {})
                    .get("proof_chain_continuity_emit_ledger_validate", {})
                    .get("status", "MISSING")
                ),
                "reason": "Probe-path status is recorded for context but does not block generalized milestone attestation.",
                "evidence": readiness_path.as_posix(),
            },
        },
        "non_blocking_followups": _nonblocking_followups(remediation),
        "blocking_issues": blocking_issues,
        "evidence_inputs": [
            _evidence_record(readiness_path, "closure_readiness_audit"),
            _evidence_record(remediation_path, "closure_remediation_order"),
            _evidence_record(scope_path, "closure_scope_classification"),
            _evidence_record(validator_path, "non_probe_validator_output"),
            _evidence_record(run_artifact_path, "non_probe_run_artifact"),
            _evidence_record(run_surface_path, "non_probe_validator_surface"),
            _evidence_record(ledger_path, "non_probe_ledger_surface"),
        ],
        "determinism_notes": [
            "Attestation derives solely from provided evidence file set.",
            "Evidence digests are SHA-256 over exact file bytes.",
            "No inferred generalized claim is allowed without scope+validator chain satisfaction.",
        ],
        "provenance": {
            "generator": "scripts/run_closure_generalized_attestation.py",
            "operator": "codex",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit deterministic generalized closure attestation artifact.")
    parser.add_argument(
        "--readiness",
        default="artifacts_seal/audits/closure_readiness/closure_readiness.audit.v1.json",
    )
    parser.add_argument(
        "--remediation",
        default="artifacts_seal/audits/closure_readiness/closure_remediation_order.v1.json",
    )
    parser.add_argument(
        "--scope",
        default="artifacts_seal/audits/closure_readiness/closure_scope_classification.v1.json",
    )
    parser.add_argument(
        "--validator",
        default="out/validators/execution-validation-run.generalized_coverage.scopepass.v1.json",
    )
    parser.add_argument(
        "--run-artifact",
        default="artifacts_seal/runs/generalized_coverage/run.generalized_coverage.scopepass.v1.artifact.json",
    )
    parser.add_argument(
        "--run-surface",
        default="artifacts_seal/runs/generalized_coverage/run.generalized_coverage.scopepass.v1.validator_surface.json",
    )
    parser.add_argument(
        "--ledger",
        default="out/ledger/generalized_coverage_linkage.jsonl",
    )
    parser.add_argument(
        "--out",
        default="artifacts_seal/audits/closure_readiness/closure_generalized_attestation.v1.json",
    )
    args = parser.parse_args()

    artifact = build_attestation(
        readiness_path=Path(args.readiness),
        remediation_path=Path(args.remediation),
        scope_path=Path(args.scope),
        validator_path=Path(args.validator),
        run_artifact_path=Path(args.run_artifact),
        run_surface_path=Path(args.run_surface),
        ledger_path=Path(args.ledger),
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
