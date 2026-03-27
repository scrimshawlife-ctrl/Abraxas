from __future__ import annotations

from pathlib import Path

import pytest

from abx.coupling_audit import audit_coupling
from abx.ers_scheduler import ERSTask, run_scheduler
from abx.operator_workflows import run_operator_workflow
from abx.promotion_pack import build_promotion_pack
from abx.runtime_orchestrator import execute_run_plan


def _payload(tmp_path: Path) -> dict:
    return {
        "base_dir": str(tmp_path),
        "run_id": "RUN-OPS-001",
        "scenario_id": "SCN-OPS-001",
        "events": [
            {"forecast_id": "f-1", "asset_id": "BTC", "score": 0.8, "confidence": 0.9, "entry_price": 100.0, "exit_price": 110.0},
        ],
        "strategy_config": {"min_confidence": 0.6, "position_risk_fraction": 0.1, "max_notional": 1000.0},
        "lane": "SHADOW",
        "influence_policy": "NONE",
        "influences_active_path": False,
        "promotion_evidence": {
            "contract_present": True,
            "tests_present": True,
            "invariance_present": True,
            "proof_present": True,
            "lineage_present": True,
            "canary_passed": True,
        },
        "current_lane": "CANARY",
        "target_lane": "ACTIVE",
    }


def test_runtime_orchestrator_is_deterministic(tmp_path: Path) -> None:
    payload = _payload(tmp_path)
    a = execute_run_plan(payload)
    b = execute_run_plan(payload)
    assert a["workflow"]["summary_hash"] == b["workflow"]["summary_hash"]
    assert a["run_plan"]["phases"] == b["run_plan"]["phases"]


def test_ers_scheduler_requires_metadata() -> None:
    tasks = [ERSTask(task_id="t1", phase="simulation", priority=1, fn=lambda: {"ok": True}, metadata={})]
    with pytest.raises(ValueError, match="missing_scheduler_metadata"):
        run_scheduler(run_id="RUN-SCHED", policy_id="ERS.v1", tasks=tasks, require_metadata=True)


def test_coupling_audit_stable(tmp_path: Path) -> None:
    a = audit_coupling(repo_root=Path("."))
    b = audit_coupling(repo_root=Path("."))
    assert a.coupling_map == b.coupling_map


def test_operator_workflows_and_promotion_pack(tmp_path: Path) -> None:
    payload = _payload(tmp_path)

    orchestration = run_operator_workflow("run-runtime-orchestrator-workflow", payload)
    assert orchestration["workflow"]["artifact_type"] == "WorkflowExecutionArtifact.v1"

    coupling = run_operator_workflow("run-coupling-audit-workflow", payload)
    assert coupling["artifact_type"] == "CouplingAuditArtifact.v1"

    pack = build_promotion_pack(payload)
    assert pack.artifact_type == "PromotionPackArtifact.v1"
    assert pack.readiness in {"READY", "BLOCKED"}
    assert pack.pack_hash
