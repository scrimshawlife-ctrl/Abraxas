from __future__ import annotations

from abx.artifacts.scoping import build_scoped_registry
from abx.continuity import build_continuity_record
from abx.ers_scheduler import ERSTask
from abx.runtime.concurrency import execute_overlap_safe_workflows
from abx.runtime.runIsolation import build_concurrency_boundary, build_run_context, isolate_payload
from abx.scheduler.scaleHandling import run_partitioned_scheduler
from abx.scale.scorecard import build_scale_coherence_scorecard


def test_concurrent_run_isolation_enforces_run_id() -> None:
    run_a = build_run_context(run_id="RUN-A", scenario_id="SCN")
    run_b = build_run_context(run_id="RUN-B", scenario_id="SCN")

    assert run_a.run_id != run_b.run_id
    assert build_concurrency_boundary(run_a).artifact_scope != build_concurrency_boundary(run_b).artifact_scope
    assert isolate_payload({}, run_a)["run_id"] == "RUN-A"


def test_artifact_collision_detection() -> None:
    report = build_scoped_registry({"RUN-A": ["artifact-1", "artifact-1"], "RUN-B": ["artifact-1"]})
    assert report["collisions"] == ["RUN-A:artifact-1"]


def test_scheduler_ordering_stability() -> None:
    ctx = build_run_context(run_id="RUN-A", scenario_id="SCN")
    tasks = {
        "RUN-A": [
            ERSTask("b", "simulation", 10, fn=lambda: "b", metadata={"pressure": 0.2, "precedence": 1}),
            ERSTask("a", "simulation", 10, fn=lambda: "a", metadata={"pressure": 0.2, "precedence": 0}),
        ]
    }
    a = run_partitioned_scheduler(contexts=[ctx], task_factory=tasks)
    b = run_partitioned_scheduler(contexts=[ctx], task_factory=tasks)
    assert a == b
    assert a["runs"][0]["scheduler"]["ordered_task_ids"] == ["RUN-A:a", "RUN-A:b"]


def test_workflow_overlap_safety(monkeypatch) -> None:
    monkeypatch.setattr(
        "abx.runtime.concurrency.run_operator_workflow",
        lambda workflow, payload: {"artifactId": f"{payload['run_id']}-{workflow}"},
    )
    ctx = build_run_context(run_id="RUN-A", scenario_id="SCN")
    result = execute_overlap_safe_workflows(ctx, [("inspect-proof-workflow", {}), ("inspect-proof-workflow", {})])
    assert result["ordered_workflows"] == ["inspect-proof-workflow"]
    assert len(result["artifacts"]) == 1


def test_continuity_consistency_rules() -> None:
    inherit = build_run_context(run_id="RUN-B", scenario_id="SCN", previous_run_id="RUN-A", inherit_continuity=True)
    isolate = build_run_context(run_id="RUN-C", scenario_id="SCN", previous_run_id="RUN-A", inherit_continuity=False)

    inherit_record = build_continuity_record(inherit.__dict__)
    isolate_record = build_continuity_record(isolate.__dict__)
    assert inherit_record.previous_run_id == "RUN-A"
    assert isolate_record.previous_run_id == "RUN-A"
    assert inherit.continuity_mode == "INHERIT"
    assert isolate.continuity_mode == "ISOLATE"


def test_invariance_under_parallel_execution(monkeypatch) -> None:
    monkeypatch.setattr(
        "abx.runtime.concurrency.run_operator_workflow",
        lambda workflow, payload: {"artifactId": f"{payload['run_id']}-{workflow}"},
    )

    contexts = [
        build_run_context(run_id="RUN-A", scenario_id="SCN"),
        build_run_context(run_id="RUN-B", scenario_id="SCN"),
    ]
    scheduler = run_partitioned_scheduler(
        contexts=contexts,
        task_factory={
            "RUN-A": [ERSTask("a", "simulation", 1, fn=lambda: "ok", metadata={"pressure": 0.1, "precedence": 0})],
            "RUN-B": [ERSTask("a", "simulation", 1, fn=lambda: "ok", metadata={"pressure": 0.1, "precedence": 0})],
        },
    )
    workflow_runs = [execute_overlap_safe_workflows(ctx, [("inspect-proof-workflow", {})]) for ctx in contexts]
    continuity_rows = [
        {"run_id": "RUN-A", "continuity_status": "PARTIAL", "summary_hash": "x"},
        {"run_id": "RUN-B", "continuity_status": "PARTIAL", "summary_hash": "y"},
    ]

    score_a = build_scale_coherence_scorecard(
        contexts=contexts,
        scheduler_inspection=scheduler,
        workflow_runs=workflow_runs,
        continuity_rows=continuity_rows,
    )
    score_b = build_scale_coherence_scorecard(
        contexts=contexts,
        scheduler_inspection=scheduler,
        workflow_runs=workflow_runs,
        continuity_rows=continuity_rows,
    )
    assert score_a.__dict__ == score_b.__dict__
