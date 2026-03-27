#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from abx.continuity import build_continuity_summary
from abx.ers_scheduler import ERSTask
from abx.runtime.concurrency import execute_overlap_safe_workflows
from abx.runtime.runIsolation import build_run_context
from abx.scale.scorecard import build_scale_coherence_scorecard
from abx.scheduler.scaleHandling import run_partitioned_scheduler


def _task_factory(run_id: str):
    return [
        ERSTask(
            task_id="phase.simulation",
            phase="simulation",
            priority=100,
            metadata={"pressure": 0.2, "precedence": 0},
            fn=lambda rid=run_id: {"artifactId": f"simulation-{rid}"},
        )
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit deterministic scale coherence scorecard")
    parser.add_argument("--scenario-id", default="scale-pass12")
    parser.add_argument("--run-ids", nargs="+", default=["RUN-A", "RUN-B"])
    parser.add_argument("--base-dir", default=".")
    args = parser.parse_args()

    contexts = [build_run_context(run_id=run_id, scenario_id=args.scenario_id) for run_id in sorted(set(args.run_ids))]
    scheduler = run_partitioned_scheduler(
        contexts=contexts,
        task_factory={ctx.run_id: _task_factory(ctx.run_id) for ctx in contexts},
    )
    workflow_runs = [
        execute_overlap_safe_workflows(ctx, [("inspect-proof-workflow", {"scenario_id": args.scenario_id})])
        for ctx in contexts
    ]
    continuity_rows = [
        build_continuity_summary(base_dir=Path(args.base_dir), payload={"run_id": ctx.run_id, "scenario_id": args.scenario_id}).__dict__
        for ctx in contexts
    ]

    scorecard = build_scale_coherence_scorecard(
        contexts=contexts,
        scheduler_inspection=scheduler,
        workflow_runs=workflow_runs,
        continuity_rows=continuity_rows,
    )

    print(json.dumps(scorecard.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
