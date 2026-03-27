from __future__ import annotations

from pathlib import Path

from abx.continuity import build_continuity_summary
from abx.frame_adapters import adapter_audit, assemble_resonance_frame
from abx.operator_workflows import run_operator_workflow


def _payload(tmp_path: Path) -> dict:
    return {
        "base_dir": str(tmp_path),
        "run_id": "RUN-FRAME-001",
        "scenario_id": "SCN-FRAME-001",
        "previous_run_id": "RUN-FRAME-000",
        "events": [
            {"forecast_id": "f-1", "asset_id": "BTC", "score": 0.8, "confidence": 0.9, "entry_price": 100.0, "exit_price": 110.0},
        ],
        "strategy_config": {"min_confidence": 0.6, "position_risk_fraction": 0.1, "max_notional": 1000.0},
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


def test_frame_assembly_is_deterministic(tmp_path: Path) -> None:
    payload = _payload(tmp_path)
    a = assemble_resonance_frame(payload)
    b = assemble_resonance_frame(payload)

    assert a["frame"]["frame_hash"] == b["frame"]["frame_hash"]
    assert a["projection"]["frame_hash"] == b["projection"]["frame_hash"]


def test_adapter_audit_stable() -> None:
    a = adapter_audit()
    b = adapter_audit()
    assert a == b


def test_continuity_summary_and_operator_frame_workflow(tmp_path: Path) -> None:
    payload = _payload(tmp_path)
    run_operator_workflow("run-simulation-workflow", payload)

    continuity = build_continuity_summary(base_dir=tmp_path, payload=payload)
    assert continuity.continuity_status in {"VALID", "PARTIAL", "BROKEN"}
    assert continuity.chain[0] == "RUN-FRAME-000"

    frame = run_operator_workflow("inspect-current-frame", payload)
    assert frame["frame"]["frame_type"] == "ResonanceFrame.v1"
    assert frame["projection"]["projection_type"] == "FrameProjection.v1"

    continuity_view = run_operator_workflow("inspect-continuity", payload)
    assert continuity_view["artifact_type"] == "ContinuitySummaryArtifact.v1"
