from __future__ import annotations

from typing import Any, Dict, List, Mapping

from abx.proof.artifact_writer import write_json_artifact
from abx.repair.noop_executor import run_noop_executor
from abx.repair.planner import build_repair_manifest
from abx.repair.receipt_binding import build_patch004_receipt_binding, write_patch004_binding_artifacts

_SCENARIOS = [
    ("scn_001", "POLICY_REFINEMENT", ["abx/operator/review_builder.py"], "Refine policy mapping", "MEDIUM", "Improve severity precision"),
    ("scn_002", "TEST_EXPANSION", ["tests/test_operator_queue.py"], "Expand policy tests", "LOW", "Increase confidence via coverage"),
    ("scn_003", "PROOF_VISIBILITY_AUDIT", ["abx/viz/proof_builder.py"], "Audit visibility contracts", "LOW", "Strengthen proof observability"),
    ("scn_004", "CONFIDENCE_THRESHOLD_STUDY", ["scripts/run_multi_cycle_replay.py"], "Study confidence threshold effects", "MEDIUM", "Improve review signal stability"),
    ("scn_005", "DOCS_ONLY", ["docs/patch004_design_scaffold.md"], "Document patch004 assumptions", "LOW", "Reduce operator ambiguity"),
    ("scn_006", "NOOP_BASELINE", ["abx/repair/noop_executor.py"], "Baseline no-op scenario", "LOW", "Control baseline for comparison"),
]
_RISK_PENALTY = {"LOW": 0.0, "MEDIUM": 0.2, "HIGH": 0.4}
_BONUS = {
    "PROOF_VISIBILITY_AUDIT": 0.15,
    "TEST_EXPANSION": 0.12,
    "POLICY_REFINEMENT": 0.10,
    "CONFIDENCE_THRESHOLD_STUDY": 0.08,
    "DOCS_ONLY": 0.04,
    "NOOP_BASELINE": 0.00,
}


def generate_starter_scenarios() -> List[Dict[str, Any]]:
    out = []
    for sid, stype, targets, obj, risk, benefit in _SCENARIOS:
        out.append({
            "schema_version": "ScenarioSpec.v1", "scenario_id": sid, "scenario_type": stype,
            "readiness_status": "READY_FOR_DESIGN", "design_pass_allowed": True,
            "execution_allowed": False, "runtime_mutation_allowed": False,
            "objective": obj, "proposed_targets": targets, "risk_level": risk,
            "expected_benefit": benefit, "operator_review_required": True,
        })
    return out


def _score(binding_status: str, scenario_type: str, risk: str) -> float:
    base = 1.0 if binding_status == "BOUND" else 0.0
    return max(0.0, min(1.0, base + _BONUS.get(scenario_type, 0.0) - _RISK_PENALTY.get(risk, 0.4)))


def run_scenario_batch(*, write_artifacts: bool = False, scenario_set: str = "starter") -> Dict[str, Any]:
    assert scenario_set == "starter"
    scenarios = generate_starter_scenarios()
    results = []
    for scn in scenarios:
        summary = {
            "run_id": scn["scenario_id"], "readiness_status": scn["readiness_status"], "design_pass_allowed": scn["design_pass_allowed"],
            "execution_allowed": False, "runtime_mutation_allowed": False,
            "execution_triggered": False, "runtime_mutation": False, "authority_leak_detected": False,
            "cycle_count_observed": 30,
        }
        manifest = build_repair_manifest(summary)
        receipt = run_noop_executor(manifest)
        binding = build_patch004_receipt_binding(receipt, manifest=manifest)
        if write_artifacts:
            meta = write_patch004_binding_artifacts(str(receipt["run_id"]), manifest, receipt)
            binding = meta["binding"]
            write_json_artifact(scn, f"out/repair/patch004/{receipt['run_id']}/{scn['scenario_id']}.scenario.json")
        score = _score(binding["binding_status"], scn["scenario_type"], scn["risk_level"])
        status = "PASS" if binding["binding_status"] == "BOUND" else binding["binding_status"]
        results.append({
            "schema_version": "ScenarioResult.v1", "scenario_id": scn["scenario_id"], "scenario_type": scn["scenario_type"],
            "manifest_id": manifest["manifest_id"], "receipt_run_id": receipt["run_id"], "binding_id": binding["binding_id"],
            "actions_planned": receipt["actions_planned"], "actions_executed": 0, "files_modified": [],
            "binding_status": binding["binding_status"], "scenario_status": status, "risk_level": scn["risk_level"],
            "score": score, "rank_reason": "deterministic_score", "execution_allowed": False, "runtime_mutation_allowed": False,
            "safety_flags": {"execution_triggered": False, "runtime_mutation": False, "authority_leak_detected": False},
        })

    risk_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    results = sorted(results, key=lambda r: (-r["score"], risk_rank[r["risk_level"]], r["scenario_id"]))
    pass_count = sum(1 for r in results if r["scenario_status"] == "PASS")
    blocked_count = sum(1 for r in results if r["scenario_status"] != "PASS")
    top_id = results[0]["scenario_id"] if results else "NOT_COMPUTABLE"
    return {
        "schema_version": "ScenarioBatchReport.v1", "batch_id": "patch004-scenario-batch-starter", "scenario_count": len(results),
        "pass_count": pass_count, "blocked_count": blocked_count, "top_scenario_id": top_id, "results": results,
        "execution_allowed": False, "runtime_mutation_allowed": False, "production_ready": False,
        "recommended_next_action": "promote top ranked sandbox scenario to operator review",
    }
