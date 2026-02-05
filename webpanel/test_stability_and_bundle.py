from __future__ import annotations

import zipfile
from io import BytesIO

from fastapi.testclient import TestClient

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, DeferralStart
from webpanel.policy import get_policy_snapshot
from webpanel.store import InMemoryStore
from webpanel.stability import run_stabilization


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


def _run_extract_compress(run_id: str) -> None:
    webpanel_app._start_deferral(run_id, DeferralStart(quota_max_actions=3))
    webpanel_app._step_deferral(run_id)
    webpanel_app._step_deferral(run_id)


def test_stability_and_bundle():
    webpanel_app.reset_state(store=InMemoryStore(), ledger=LedgerChain())
    _STEP_STATE.clear()

    resp_a = webpanel_app.ingest(_packet("sig-a", {"a": 1, "url": "https://x"}))
    _run_extract_compress(resp_a["run_id"])

    resp_b = webpanel_app._ingest_packet(
        _packet("sig-b", {"a": 2, "b": 3, "url": "https://x"}),
        prev_run_id=resp_a["run_id"],
    )
    _run_extract_compress(resp_b["run_id"])

    run_a = webpanel_app.store.get(resp_a["run_id"])
    run_b = webpanel_app.store.get(resp_b["run_id"])
    assert run_a is not None and run_b is not None

    snapshot = get_policy_snapshot()
    run_a.stability_report = run_stabilization(
        run_a,
        cycles=12,
        operators=["extract_structure_v0", "compress_signal_v0", "propose_actions_v0"],
        policy_hash=snapshot["policy_hash"],
        prior_report=None,
    )
    run_b.stability_report = run_stabilization(
        run_b,
        cycles=12,
        operators=["extract_structure_v0", "compress_signal_v0", "propose_actions_v0"],
        policy_hash=snapshot["policy_hash"],
        prior_report=None,
    )

    client = TestClient(webpanel_app.app)
    bundle_resp = client.get(f"/export/bundle?left={run_a.run_id}&right={run_b.run_id}")
    assert bundle_resp.status_code == 200

    buf = BytesIO(bundle_resp.content)
    with zipfile.ZipFile(buf, "r") as zf:
        names = set(zf.namelist())
    assert "stability.left.json" in names
    assert "stability.right.json" in names
    assert "manifest.json" in names
    assert "run_brief.json" in names
    assert "policy.left_at_ingest.json" in names
    assert "policy.right_at_ingest.json" in names
