from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List

from webpanel.compress_signal import (
    build_uncertainty_map,
    classify_refs,
    compute_plan_pressure,
    next_questions,
    pick_salient_metrics,
    recommended_mode,
)
from webpanel.models import RunState
from webpanel.propose_actions import propose_actions
from webpanel.structure_extract import detect_unknowns, extract_claims_if_present, walk_payload


def canonical_bytes(obj: Any) -> bytes:
    rendered = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return rendered.encode("utf-8")


def stable_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def clone_run_state(run: RunState) -> RunState:
    return deepcopy(run)


def _extract_structure(run: RunState) -> Dict[str, Any]:
    payload = run.signal.payload
    extract = walk_payload(payload)
    unknowns = detect_unknowns(payload)
    claims = extract_claims_if_present(payload if isinstance(payload, dict) else {})
    paths = extract["paths"]
    sample_paths = [entry["path"] for entry in paths[:25]]
    numeric_metrics = extract["numeric_metrics"][:25]
    evidence_refs = extract["string_refs"][:25]
    unknowns_out = unknowns[:25]
    return {
        "kind": "extract_structure_v0",
        "keys_topology": {"paths_count": len(paths), "sample_paths": sample_paths},
        "paths": [entry["path"] for entry in paths],
        "numeric_metrics": numeric_metrics,
        "unknowns": unknowns_out,
        "evidence_refs": evidence_refs,
        "claims_present": len(claims) > 0,
        "claims_preview": claims[:5],
    }


def _compress_signal(run: RunState, extracted: Dict[str, Any]) -> Dict[str, Any]:
    signal_meta = {
        "lane": run.signal.lane,
        "invariance_status": run.signal.invariance_status,
        "provenance_status": run.signal.provenance_status,
        "drift_flags": list(run.signal.drift_flags),
    }
    ctx = {"unknowns": list(run.context.unknowns)}
    plan_pressure = compute_plan_pressure(signal_meta, ctx, extracted)
    salient_metrics = pick_salient_metrics(extracted.get("numeric_metrics", []))
    uncertainty_map = build_uncertainty_map(extracted.get("unknowns", []), ctx["unknowns"])
    evidence_surface = classify_refs(extracted.get("evidence_refs", []))
    mode = recommended_mode(signal_meta, plan_pressure["score"])
    questions = next_questions(signal_meta, extracted, uncertainty_map)
    return {
        "kind": "compress_signal_v0",
        "plan_pressure": plan_pressure,
        "salient_metrics": salient_metrics,
        "uncertainty_map": uncertainty_map,
        "evidence_surface": evidence_surface,
        "recommended_mode": mode,
        "next_questions": questions,
    }


def _propose_actions(run: RunState, compressed: Dict[str, Any]) -> Dict[str, Any]:
    signal_meta = {
        "lane": run.signal.lane,
        "invariance_status": run.signal.invariance_status,
        "provenance_status": run.signal.provenance_status,
        "drift_flags": list(run.signal.drift_flags),
    }
    actions = propose_actions(
        signal_meta=signal_meta,
        compressed=compressed,
        requires_human_confirmation=run.requires_human_confirmation,
    )
    return {
        "kind": "propose_actions_v0",
        "actions": [action.model_dump() for action in actions],
    }


def run_stabilization(run: RunState, cycles: int) -> Dict[str, Any]:
    clone = clone_run_state(run)
    created_at_utc = datetime.now(timezone.utc).isoformat()
    operators = ["extract_structure_v0", "compress_signal_v0", "propose_actions_v0"]

    results: List[Dict[str, Any]] = []
    final_hashes: List[str] = []

    for cycle in range(cycles):
        extract = _extract_structure(clone)
        compress = _compress_signal(clone, extract)
        propose = _propose_actions(clone, compress)
        operator_hashes = {
            "extract_structure_v0": stable_hash(extract),
            "compress_signal_v0": stable_hash(compress),
            "propose_actions_v0": stable_hash(propose),
        }
        final_hash = stable_hash(
            {
                "extract_structure_v0": extract,
                "compress_signal_v0": compress,
                "propose_actions_v0": propose,
            }
        )
        final_hashes.append(final_hash)
        results.append(
            {
                "cycle": cycle,
                "operator_hashes": operator_hashes,
                "final_hash": final_hash,
            }
        )

    leader_hash = final_hashes[0] if final_hashes else ""
    distinct = len(set(final_hashes))
    mismatched_cycles = [
        result["cycle"] for result in results if result["final_hash"] != leader_hash
    ]
    passed = distinct == 1
    drift_class = "none" if passed else "nondeterminism"

    report = {
        "kind": "StabilityReport.v0",
        "report_id": f"stb_{stable_hash({'run_id': run.run_id, 'created_at_utc': created_at_utc, 'cycles': cycles})[:16]}",
        "run_id": run.run_id,
        "created_at_utc": created_at_utc,
        "cycles": cycles,
        "operators": operators,
        "results": results,
        "invariance": {
            "passed": passed,
            "distinct_final_hashes": distinct,
            "leader_hash": leader_hash,
            "mismatched_cycles": mismatched_cycles,
        },
        "drift_class": drift_class,
        "notes": "Stability harness run on deterministic operators only.",
    }
    return report
