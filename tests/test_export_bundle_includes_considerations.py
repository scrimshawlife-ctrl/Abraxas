from __future__ import annotations

import json
import zipfile
from io import BytesIO

from webpanel.compare import compare_runs
from webpanel.core_bridge import core_ingest
from webpanel.export_bundle import build_bundle
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, RunState
from webpanel.policy import get_policy_snapshot


def _packet(signal_id: str, payload: dict) -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id=signal_id,
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload=payload,
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def _run(signal_id: str, payload: dict) -> RunState:
    result = core_ingest(_packet(signal_id, payload).model_dump())
    return RunState(**result)


def _proposal(action_id: str) -> dict:
    return {
        "action_id": action_id,
        "kind": "request_missing_integrity",
        "title": "Request missing integrity evidence",
        "rationale": ["reason-a"],
        "required_gates": ["ack_required"],
        "expected_entropy_reduction": 0.5,
        "risk_notes": "low risk",
        "preview_effect": {},
    }


def test_export_bundle_includes_considerations():
    left = _run("sig-left", {"a": 1})
    right = _run("sig-right", {"a": 2})
    left.step_results = [{"kind": "propose_actions_v0", "actions": [_proposal("act_left")]}]
    left.last_step_result = left.step_results[-1]
    right.step_results = [{"kind": "propose_actions_v0", "actions": [_proposal("act_right")]}]
    right.last_step_result = right.step_results[-1]

    compare_summary = compare_runs(left, right)
    policy_snapshot = get_policy_snapshot()
    ledger = LedgerChain()

    bundle_bytes = build_bundle(
        left_run=left,
        right_run=right,
        compare_summary=compare_summary,
        policy_snapshot=policy_snapshot,
        ledger_store=ledger,
    )

    buf = BytesIO(bundle_bytes)
    with zipfile.ZipFile(buf, "r") as zf:
        names = set(zf.namelist())
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))

    assert "considerations.json" in names
    assert "considerations_sha256" in manifest
