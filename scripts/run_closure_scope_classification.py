#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Mapping, Tuple

ScopeStatus = Literal[
    "PROBE_PATH_CONFIRMED",
    "GENERALIZED_CONFIRMED",
    "PARTIAL_SCOPE_ONLY",
    "UNCOVERED_SURFACES",
    "BLOCKED_BY_SURFACE_MISMATCH",
]


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected dict JSON at {path.as_posix()}")
    return payload


def _collect_json(path_glob: Path) -> List[Tuple[Path, Dict[str, Any]]]:
    output: List[Tuple[Path, Dict[str, Any]]] = []
    for path in sorted(path_glob.parent.glob(path_glob.name)):
        try:
            payload = _load_json(path)
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        output.append((path, payload))
    return output


def _axis_status(audit: Mapping[str, Any], axis: str) -> str:
    block = audit.get("classifications", {}).get(axis, {})
    if isinstance(block, Mapping):
        return str(block.get("status", "MISSING"))
    return "MISSING"


def _probe_path_confirmed(audit: Mapping[str, Any]) -> bool:
    required_axes = (
        "proof_chain_continuity_emit_ledger_validate",
        "correlation_pointer_sufficiency",
        "promotion_relevant_evidence_sufficiency",
    )
    return all(_axis_status(audit, axis) == "SATISFIED" for axis in required_axes)


def _is_probe_run_id(run_id: str) -> bool:
    return run_id.startswith("run.compliance_probe")


def _has_generalized_closure_evidence(
    validator_outputs: List[Tuple[Path, Dict[str, Any]]],
) -> Tuple[bool, List[str], List[str], List[str]]:
    generalized_runs: List[str] = []
    partial_runs: List[str] = []
    uncovered: List[str] = []

    non_probe = []
    for path, payload in validator_outputs:
        run_id = str(payload.get("runId", ""))
        if not run_id or _is_probe_run_id(run_id):
            continue
        non_probe.append((path, payload, run_id))

    if not non_probe:
        uncovered.append("out/validators/execution-validation-*.json has no non-probe run outputs")
        return False, generalized_runs, partial_runs, uncovered

    for path, payload, run_id in non_probe:
        validated = payload.get("validatedArtifacts", [])
        correlation = payload.get("correlation", {})
        ledger_ids = correlation.get("ledgerIds", []) if isinstance(correlation, Mapping) else []
        pointers = correlation.get("pointers", []) if isinstance(correlation, Mapping) else []

        has_validated = isinstance(validated, list) and len(validated) > 0
        has_ledger_ids = isinstance(ledger_ids, list) and len(ledger_ids) > 0
        has_pointers = isinstance(pointers, list) and len(pointers) > 0

        if has_validated and has_ledger_ids and has_pointers:
            generalized_runs.append(run_id)
        else:
            partial_runs.append(
                f"{run_id}::{path.as_posix()}::validated={int(has_validated)}::ledgerIds={int(has_ledger_ids)}::pointers={int(has_pointers)}"
            )

    if generalized_runs:
        return True, sorted(set(generalized_runs)), sorted(set(partial_runs)), uncovered

    if partial_runs:
        return False, generalized_runs, sorted(set(partial_runs)), uncovered

    uncovered.append("non-probe validator outputs were present but unusable for closure checks")
    return False, generalized_runs, partial_runs, uncovered


def build_scope_classification(*, base_dir: Path, audit_path: Path) -> Dict[str, Any]:
    audit = _load_json(audit_path)

    scope = str(audit.get("audit_scope", ""))
    scope_mentions_probe = "compliance_probe" in scope
    scope_mentions_general = "general" in scope.lower() or "proof-run" in scope.lower()

    validator_outputs = _collect_json(base_dir / "out/validators/execution-validation-*.json")

    categories: Dict[ScopeStatus, Dict[str, Any]] = {
        "PROBE_PATH_CONFIRMED": {"status": "MISSING", "reason": "", "evidence": []},
        "GENERALIZED_CONFIRMED": {"status": "MISSING", "reason": "", "evidence": []},
        "PARTIAL_SCOPE_ONLY": {"status": "MISSING", "reason": "", "evidence": []},
        "UNCOVERED_SURFACES": {"status": "MISSING", "reason": "", "evidence": []},
        "BLOCKED_BY_SURFACE_MISMATCH": {"status": "MISSING", "reason": "", "evidence": []},
    }

    blocked: List[str] = []
    if not scope_mentions_probe:
        blocked.append("closure_readiness audit_scope does not declare compliance_probe coverage")
    if scope_mentions_general:
        blocked.append(
            "closure_readiness audit_scope appears generalized; this pass requires explicit probe-vs-general distinction"
        )

    probe_confirmed = _probe_path_confirmed(audit)
    generalized_confirmed, generalized_runs, generalized_partial, generalized_uncovered = _has_generalized_closure_evidence(
        validator_outputs
    )

    if probe_confirmed:
        categories["PROBE_PATH_CONFIRMED"] = {
            "status": "SATISFIED",
            "reason": "Probe-path closure gate is satisfied via readiness audit axes.",
            "evidence": [
                f"{audit_path.as_posix()}#proof_chain_continuity_emit_ledger_validate:{_axis_status(audit, 'proof_chain_continuity_emit_ledger_validate')}",
                f"{audit_path.as_posix()}#correlation_pointer_sufficiency:{_axis_status(audit, 'correlation_pointer_sufficiency')}",
                f"{audit_path.as_posix()}#promotion_relevant_evidence_sufficiency:{_axis_status(audit, 'promotion_relevant_evidence_sufficiency')}",
            ],
        }
    else:
        categories["PROBE_PATH_CONFIRMED"] = {
            "status": "MISSING",
            "reason": "Probe-path closure gate is not fully satisfied in readiness audit.",
            "evidence": [
                f"{audit_path.as_posix()}#proof_chain_continuity_emit_ledger_validate:{_axis_status(audit, 'proof_chain_continuity_emit_ledger_validate')}",
                f"{audit_path.as_posix()}#correlation_pointer_sufficiency:{_axis_status(audit, 'correlation_pointer_sufficiency')}",
                f"{audit_path.as_posix()}#promotion_relevant_evidence_sufficiency:{_axis_status(audit, 'promotion_relevant_evidence_sufficiency')}",
            ],
        }

    if generalized_confirmed:
        categories["GENERALIZED_CONFIRMED"] = {
            "status": "SATISFIED",
            "reason": "At least one non-probe run has validator-visible validatedArtifacts + ledgerIds + pointers.",
            "evidence": generalized_runs,
        }
    else:
        categories["GENERALIZED_CONFIRMED"] = {
            "status": "MISSING",
            "reason": "No direct non-probe closure evidence met generalized confirmation criteria.",
            "evidence": generalized_partial[:20],
        }

    if probe_confirmed and not generalized_confirmed:
        categories["PARTIAL_SCOPE_ONLY"] = {
            "status": "SATISFIED",
            "reason": "Current closure-grade evidence is probe-path confirmed but not generalized.",
            "evidence": ["probe_confirmed=1", "generalized_confirmed=0"],
        }
    elif probe_confirmed and generalized_confirmed:
        categories["PARTIAL_SCOPE_ONLY"] = {
            "status": "MISSING",
            "reason": "Closure evidence includes generalized non-probe confirmation.",
            "evidence": ["probe_confirmed=1", "generalized_confirmed=1"],
        }
    else:
        categories["PARTIAL_SCOPE_ONLY"] = {
            "status": "MISSING",
            "reason": "Probe path itself is not fully confirmed; cannot classify as partial-only.",
            "evidence": ["probe_confirmed=0"],
        }

    uncovered = list(generalized_uncovered)
    if generalized_partial:
        uncovered.append("non-probe outputs exist but are partial for closure criteria")

    categories["UNCOVERED_SURFACES"] = {
        "status": "SATISFIED" if uncovered else "MISSING",
        "reason": "Surfaces lacking direct closure proof are explicitly enumerated."
        if uncovered
        else "No uncovered surfaces detected by deterministic checks.",
        "evidence": sorted(set(uncovered + generalized_partial))[:50],
    }

    categories["BLOCKED_BY_SURFACE_MISMATCH"] = {
        "status": "SATISFIED" if blocked else "MISSING",
        "reason": "Audit scope/contract mismatch prevents reliable scope classification."
        if blocked
        else "No blocking scope mismatch detected.",
        "evidence": blocked,
    }

    summary_status: ScopeStatus
    if blocked:
        summary_status = "BLOCKED_BY_SURFACE_MISMATCH"
    elif generalized_confirmed:
        summary_status = "GENERALIZED_CONFIRMED"
    elif probe_confirmed and not generalized_confirmed:
        summary_status = "PARTIAL_SCOPE_ONLY"
    elif uncovered:
        summary_status = "UNCOVERED_SURFACES"
    else:
        summary_status = "PROBE_PATH_CONFIRMED"

    return {
        "schema_version": "aal.closure_scope_classification.v1",
        "classification_scope": {
            "source_audit_path": audit_path.as_posix(),
            "source_audit_scope": scope,
            "validator_outputs_scanned": len(validator_outputs),
        },
        "summary_status": summary_status,
        "categories": categories,
        "determinism_notes": [
            "Deterministic file discovery via sorted glob order.",
            "Generalization requires direct non-probe validator evidence; no inference from probe-only success.",
            "Missing evidence is represented explicitly as uncovered or missing categories.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify closure readiness scope: probe-path vs generalized surfaces.")
    parser.add_argument("--base-dir", default=".", help="Repository base directory")
    parser.add_argument(
        "--audit",
        default="artifacts_seal/audits/closure_readiness/closure_readiness.audit.v1.json",
        help="Path to closure readiness audit artifact",
    )
    parser.add_argument(
        "--out",
        default="artifacts_seal/audits/closure_readiness/closure_scope_classification.v1.json",
        help="Output path for scope-classification artifact",
    )
    args = parser.parse_args()

    artifact = build_scope_classification(base_dir=Path(args.base_dir), audit_path=Path(args.audit))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
