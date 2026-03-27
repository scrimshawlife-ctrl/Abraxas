from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from abx.canon_checks import run_canon_checks
from abx.closure_summary import build_closure_summary
from abx.coupling_audit import audit_coupling
from abx.invariance_harness import run_invariance_harness
from abx.operator_console import dispatch_operator_command
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


@dataclass(frozen=True)
class PromotionPackArtifact:
    artifact_type: str
    artifact_id: str
    run_id: str
    scenario_id: str
    readiness: str
    evidence: dict[str, Any]
    blockers: list[str]
    pack_hash: str


def build_promotion_pack(payload: dict[str, Any]) -> PromotionPackArtifact:
    base_dir = Path(str(payload.get("base_dir") or "."))
    run_id = str(payload.get("run_id") or "RUN-PACK")
    scenario_id = str(payload.get("scenario_id") or "SCN-PACK")

    sim = dispatch_operator_command("run-simulation", payload)
    closure = build_closure_summary(base_dir=base_dir, run_id=run_id, scenario_id=scenario_id)
    canon = run_canon_checks(payload)
    coupling = audit_coupling(repo_root=base_dir)
    invariance = run_invariance_harness(
        target="operator.run-simulation",
        runs=int(payload.get("runs") or 12),
        producer=lambda: dispatch_operator_command("run-simulation", payload),
    )

    evidence = {
        "closure_status": closure.status,
        "canon_ok": canon.ok,
        "invariance_status": invariance.status,
        "proof_chain_status": ((sim.get("proof_chain") or {}).get("status") or "NOT_COMPUTABLE"),
        "coupling_status": coupling.status,
    }

    blockers: list[str] = []
    if evidence["closure_status"] != "VALID":
        blockers.append("closure-not-valid")
    if not evidence["canon_ok"]:
        blockers.append("canon-checks-failed")
    if evidence["invariance_status"] != "VALID":
        blockers.append("invariance-not-valid")
    if evidence["proof_chain_status"] != "VALID":
        blockers.append("proof-chain-not-valid")
    if evidence["coupling_status"] == "BROKEN":
        blockers.append("coupling-audit-broken")

    readiness = "READY" if not blockers else "BLOCKED"
    payload_for_hash = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "readiness": readiness,
        "evidence": evidence,
        "blockers": sorted(blockers),
    }
    pack_hash = sha256_bytes(dumps_stable(payload_for_hash).encode("utf-8"))

    return PromotionPackArtifact(
        artifact_type="PromotionPackArtifact.v1",
        artifact_id=f"promotion-pack-{run_id}-{scenario_id}",
        run_id=run_id,
        scenario_id=scenario_id,
        readiness=readiness,
        evidence=evidence,
        blockers=sorted(blockers),
        pack_hash=pack_hash,
    )
