from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from abx.artifacts.scoping import build_scoped_registry
from abx.runtime.runIsolation import RunContext
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


@dataclass(frozen=True)
class ScaleCoherenceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str


def build_scale_coherence_scorecard(
    *,
    contexts: list[RunContext],
    scheduler_inspection: dict[str, Any],
    workflow_runs: list[dict[str, Any]],
    continuity_rows: list[dict[str, Any]],
) -> ScaleCoherenceScorecard:
    run_artifacts = {
        row["run_id"]: [item["artifact_id"] for item in row.get("artifacts", [])]
        for row in workflow_runs
    }
    scoped = build_scoped_registry(run_artifacts)

    scheduler_ok = all(len(x.get("scheduler", {}).get("ordered_task_ids", [])) > 0 for x in scheduler_inspection.get("runs", []))
    continuity_ok = all(x.get("continuity_status") in {"VALID", "PARTIAL"} for x in continuity_rows)
    overlap_safe = all(len(row.get("ordered_workflows", [])) == len(row.get("artifacts", [])) for row in workflow_runs)

    dimensions = {
        "run_isolation_integrity": "PASS" if len({x.run_id for x in contexts}) == len(contexts) else "GAP",
        "scheduler_stability": "PASS" if scheduler_ok else "GAP",
        "artifact_coherence": "PASS" if not scoped["collisions"] else "GAP",
        "workflow_collision_resistance": "PASS" if overlap_safe else "GAP",
        "continuity_consistency": "PASS" if continuity_ok else "GAP",
    }
    evidence = {
        "run_isolation_integrity": [x.context_id for x in contexts],
        "scheduler_stability": [x["scheduler_hash"] for x in scheduler_inspection.get("schedulerContexts", [])],
        "artifact_coherence": [scoped["registryHash"]],
        "workflow_collision_resistance": [x.get("summary_hash", "") for x in workflow_runs],
        "continuity_consistency": [x.get("summary_hash", "") for x in continuity_rows],
    }
    blockers = sorted([key for key, value in dimensions.items() if value != "PASS"])

    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers}
    scorecard_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return ScaleCoherenceScorecard(
        artifact_type="ScaleCoherenceScorecard.v1",
        artifact_id="scale-coherence-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=scorecard_hash,
    )
