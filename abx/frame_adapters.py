from __future__ import annotations

from pathlib import Path
from typing import Any

from abx.closure_summary import build_closure_summary
from abx.operator_console import dispatch_operator_command
from abx.promotion_pack import build_promotion_pack
from abx.resonance_frame import AdapterTransformRecord, ResonanceFrame, project_frame


def adapter_inventory() -> list[dict[str, Any]]:
    return [
        {
            "adapter_id": "adapter.simulation_to_frame",
            "source": "simulation/operator output",
            "target": "ResonanceFrame.payload",
            "status": "canonical",
            "lossy": False,
        },
        {
            "adapter_id": "adapter.closure_to_frame",
            "source": "ClosureSummaryArtifact",
            "target": "ResonanceFrame.status",
            "status": "canonical",
            "lossy": False,
        },
        {
            "adapter_id": "adapter.promotion_to_frame",
            "source": "PromotionPackArtifact",
            "target": "ResonanceFrame.evidence",
            "status": "adapted",
            "lossy": False,
        },
    ]


def adapter_audit() -> dict[str, Any]:
    inventory = adapter_inventory()
    return {
        "artifactType": "AdapterAuditArtifact.v1",
        "artifactId": "adapter-audit-runtime",
        "canonical": [x for x in inventory if x["status"] == "canonical"],
        "adapted": [x for x in inventory if x["status"] == "adapted"],
        "legacy": [x for x in inventory if x["status"] == "legacy"],
        "fragmented": [x for x in inventory if x["status"] == "fragmented"],
    }


def assemble_resonance_frame(payload: dict[str, Any]) -> dict[str, Any]:
    run_id = str(payload.get("run_id") or "RUN-FRAME")
    scenario_id = str(payload.get("scenario_id") or "SCN-FRAME")
    base_dir = Path(str(payload.get("base_dir") or "."))

    sim = dispatch_operator_command("run-simulation", payload)
    closure = build_closure_summary(base_dir=base_dir, run_id=run_id, scenario_id=scenario_id)
    pack = build_promotion_pack(payload)

    adapter_records = [
        AdapterTransformRecord(
            adapter_id="adapter.simulation_to_frame",
            source_type="OperatorSimulationOutput",
            target_type="ResonanceFrame.payload",
            lossy=False,
        ),
        AdapterTransformRecord(
            adapter_id="adapter.closure_to_frame",
            source_type="ClosureSummaryArtifact.v1",
            target_type="ResonanceFrame.status",
            lossy=False,
        ),
        AdapterTransformRecord(
            adapter_id="adapter.promotion_to_frame",
            source_type="PromotionPackArtifact.v1",
            target_type="ResonanceFrame.evidence",
            lossy=False,
        ),
    ]

    proof_chain = sim.get("proof_chain") if isinstance(sim.get("proof_chain"), dict) else {}
    validation = sim.get("validation") if isinstance(sim.get("validation"), dict) else {}
    scheduler_contexts = ((sim.get("scheduler") or {}).get("scheduler_contexts") if isinstance(sim.get("scheduler"), dict) else []) or []
    scheduler_context = scheduler_contexts[0] if scheduler_contexts else {"policy_id": "ERS.v1"}

    frame = ResonanceFrame(
        frame_type="ResonanceFrame.v1",
        frame_id=f"resonance-frame-{run_id}-{scenario_id}",
        run_id=run_id,
        scenario_id=scenario_id,
        phase="closure_summary",
        lane=str(payload.get("current_lane") or "SHADOW"),
        scheduler_context=scheduler_context,
        lineage={
            "run_id": run_id,
            "scenario_id": scenario_id,
            "proof_chain_artifact_id": proof_chain.get("artifactId"),
            "validation_artifact_id": validation.get("artifactId"),
        },
        status={
            "proof_chain_status": proof_chain.get("status"),
            "validation_status": validation.get("status"),
            "closure_status": closure.status,
        },
        evidence={
            "promotion_readiness": pack.readiness,
            "blockers": list(pack.blockers),
            "closure_evidence": dict(closure.evidence),
        },
        payload={
            "portfolio": (sim.get("simulation") or {}),
            "proof": proof_chain,
            "validation": validation,
        },
        continuity={
            "previous_run_id": payload.get("previous_run_id"),
            "carry_forward_policy": str(payload.get("carry_forward_policy") or "none"),
        },
        adapter_records=adapter_records,
    )

    projection = project_frame(frame)
    return {
        "frame": frame.__dict__ | {"frame_hash": frame.stable_hash(), "adapter_records": [r.__dict__ for r in adapter_records]},
        "projection": projection.__dict__,
        "adapter_audit": adapter_audit(),
    }
