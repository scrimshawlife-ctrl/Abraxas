from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from abx.runtime_trade_ledger import load_runtime_trade_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


@dataclass(frozen=True)
class ClosureSummaryArtifact:
    artifact_type: str
    artifact_id: str
    run_id: str
    scenario_id: str
    status: str
    artifact_counts: dict[str, int]
    evidence: dict[str, bool]
    summary_hash: str


def build_closure_summary(*, base_dir: Path, run_id: str, scenario_id: str) -> ClosureSummaryArtifact:
    rows = load_runtime_trade_records(base_dir, run_id, scenario_id)
    counts: dict[str, int] = {}
    for row in rows:
        t = str(row.get("artifact_type") or "unknown")
        counts[t] = counts.get(t, 0) + 1

    evidence = {
        "has_simulation": counts.get("SimulationArtifact.v1", 0) > 0,
        "has_validation": counts.get("ValidationResultArtifact.v1", 0) > 0,
        "has_proof_summary": counts.get("ProofSummaryArtifact.v1", 0) > 0,
        "has_forecast": counts.get("ForecastArtifact.v1", 0) > 0,
        "has_strategy": counts.get("StrategyArtifact.v1", 0) > 0,
    }

    status = "VALID" if all(evidence.values()) else ("PARTIAL" if rows else "NOT_COMPUTABLE")

    payload = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "status": status,
        "artifact_counts": counts,
        "evidence": evidence,
    }
    summary_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))

    return ClosureSummaryArtifact(
        artifact_type="ClosureSummaryArtifact.v1",
        artifact_id=f"closure-summary-{run_id}-{scenario_id}",
        run_id=run_id,
        scenario_id=scenario_id,
        status=status,
        artifact_counts=dict(sorted(counts.items())),
        evidence=evidence,
        summary_hash=summary_hash,
    )
