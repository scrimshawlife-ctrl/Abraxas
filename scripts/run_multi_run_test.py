#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from abx.continuity import build_continuity_summary
from abx.ers_scheduler import ERSTask
from abx.operator.runContext import execute_workflow_with_context
from abx.runtime.concurrency import execute_overlap_safe_workflows
from abx.runtime.runIsolation import build_concurrency_boundary, build_run_context
from abx.scheduler.scaleHandling import run_partitioned_scheduler


def _task_factory(run_id: str):
    return [
        ERSTask(
            task_id="phase.validation",
            phase="validation_proof",
            priority=90,
            metadata={"pressure": 0.2, "precedence": 1},
            fn=lambda rid=run_id: {"artifactId": f"validation-{rid}"},
        ),
        ERSTask(
            task_id="phase.simulation",
            phase="simulation",
            priority=100,
            metadata={"pressure": 0.3, "precedence": 0},
            fn=lambda rid=run_id: {"artifactId": f"simulation-{rid}"},
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic multi-run isolation/coherence simulation")
    parser.add_argument("--scenario-id", default="scale-pass12")
    parser.add_argument("--run-ids", nargs="+", default=["RUN-A", "RUN-B"])
    parser.add_argument("--base-dir", default=".")
    args = parser.parse_args()

    contexts = [build_run_context(run_id=run_id, scenario_id=args.scenario_id) for run_id in sorted(set(args.run_ids))]
    boundaries = [build_concurrency_boundary(ctx).__dict__ for ctx in contexts]

    task_factory = {ctx.run_id: _task_factory(ctx.run_id) for ctx in contexts}
    scheduler = run_partitioned_scheduler(contexts=contexts, task_factory=task_factory)

    workflow_runs = []
    operator_outputs = []
    continuity = []
    for ctx in contexts:
        overlap = execute_overlap_safe_workflows(
            ctx,
            [
                ("inspect-proof-workflow", {"scenario_id": args.scenario_id}),
                ("inspect-proof-workflow", {"scenario_id": args.scenario_id}),
                ("inspect-current-frame", {"scenario_id": args.scenario_id}),
            ],
        )
        workflow_runs.append(overlap)
        operator_outputs.append(
            execute_workflow_with_context(ctx, "inspect-current-frame", {"scenario_id": args.scenario_id})
        )
        continuity.append(
            build_continuity_summary(base_dir=Path(args.base_dir), payload={"run_id": ctx.run_id, "scenario_id": args.scenario_id}).__dict__
        )

    print(
        json.dumps(
            {
                "artifactType": "MultiRunScaleTestArtifact.v1",
                "artifactId": f"multi-run-scale-test-{args.scenario_id}",
                "contexts": [ctx.__dict__ for ctx in contexts],
                "boundaries": boundaries,
                "scheduler": scheduler,
                "workflows": workflow_runs,
                "operator_outputs": operator_outputs,
                "continuity": continuity,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
