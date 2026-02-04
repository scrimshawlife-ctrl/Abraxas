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


def _oracle_output(signal_id: str) -> dict:
    return {
        "signal_id": signal_id,
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {"score": 0.5},
        "evidence": ["ref-a"],
        "flags": {"suppressed": False},
        "provenance": {
            "input_hash": f"input-{signal_id}",
            "policy_hash": f"policy-{signal_id}",
            "operator_versions": {"extract_structure_v0": "v0"},
            "stability_status": {"passed": True, "drift_class": "none"},
        },
    }


def test_export_bundle_includes_oracle_files():
    left = _run("sig-left", {"a": 1})
    right = _run("sig-right", {"a": 2})
    left.oracle_output = _oracle_output("sig-left")
    right.oracle_output = _oracle_output("sig-right")

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

    assert "oracle.left.json" in names
    assert "oracle.right.json" in names
    assert "left_oracle_sha256" in manifest
    assert "right_oracle_sha256" in manifest
    assert "left_oracle_input_hash_prefix" in manifest
    assert "right_oracle_policy_hash_prefix" in manifest
