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


def canonical_json_bytes(obj: Any) -> bytes:
    rendered = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return rendered.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_hash(obj: Any) -> str:
    return sha256_hex(canonical_json_bytes(obj))


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


def run_stabilization(
    run: RunState,
    cycles: int,
    operators: List[str],
    policy_hash: str,
) -> Dict[str, Any]:
    clone = clone_run_state(run)
    created_at_utc = datetime.now(timezone.utc).isoformat()
    operator_order = ["extract_structure_v0", "compress_signal_v0", "propose_actions_v0"]
    selected = [op for op in operator_order if op in operators]

    results: List[Dict[str, Any]] = []
    final_hashes: List[str] = []

    for cycle in range(cycles):
        extract = _extract_structure(clone) if "extract_structure_v0" in selected else None
        compress = (
            _compress_signal(clone, extract)
            if "compress_signal_v0" in selected and extract is not None
            else None
        )
        propose = (
            _propose_actions(clone, compress)
            if "propose_actions_v0" in selected and compress is not None
            else None
        )

        operator_hashes: Dict[str, str] = {}
        final_payload: Dict[str, Any] = {}
        if extract is not None:
            operator_hashes["extract_structure_v0"] = stable_hash(extract)
            final_payload["extract_structure_v0"] = extract
        if compress is not None:
            operator_hashes["compress_signal_v0"] = stable_hash(compress)
            final_payload["compress_signal_v0"] = compress
        if propose is not None:
            operator_hashes["propose_actions_v0"] = stable_hash(propose)
            final_payload["propose_actions_v0"] = propose

        final_hash = stable_hash(final_payload)
        final_hashes.append(final_hash)
        results.append(
            {
                "cycle": cycle,
                "operator_hashes": operator_hashes,
                "final_hash": final_hash,
            }
        )

    counts: Dict[str, int] = {}
    for value in final_hashes:
        counts[value] = counts.get(value, 0) + 1
    if counts:
        leader_hash = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    else:
        leader_hash = ""
    distinct = len(counts)
    mismatched_cycles = [result["cycle"] for result in results if result["final_hash"] != leader_hash]
    passed = distinct == 1
    drift_class = "none" if passed else "nondeterminism"

    report = {
        "kind": "StabilityReport.v0",
        "report_id": f"stab_{run.run_id}_{policy_hash[:8]}",
        "run_id": run.run_id,
        "created_at_utc": created_at_utc,
        "cycles": cycles,
        "operators": selected,
        "policy_hash": policy_hash,
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
