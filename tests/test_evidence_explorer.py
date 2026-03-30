from __future__ import annotations

import json
from pathlib import Path

from abx.operator_views import build_evidence_view


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_evidence_view_inconsistent_packets(tmp_path: Path) -> None:
    run_id = "RUN-EV-1"
    manifest = tmp_path / "out" / "federated" / "manifest.json"
    _write(
        manifest,
        {
            "schema": "RemoteEvidenceManifest.v1",
            "manifest_id": "manifest-1",
            "run_id": run_id,
            "origin": "federation://cluster-a",
            "packets": [
                {"packet_id": "pkt-1", "status": "VALID", "observed_at": "2026-03-30T00:00:00+00:00", "ref": "remote://pkt/1"},
                {"packet_id": "pkt-2", "status": "FAIL", "observed_at": "2026-03-30T00:00:00+00:00", "ref": "remote://pkt/2"},
            ],
        },
    )
    _write(tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json", {"status": "VALID"})
    _write(tmp_path / "out" / "attestation" / f"canonical_proof_{run_id}.json", {"overall_status": "PASS"})
    _write(
        tmp_path / "out" / "attestation" / f"execution-attestation-{run_id}.json",
        {
            "overall_status": "PASS",
            "federated": {
                "remote_evidence_manifest": manifest.relative_to(tmp_path).as_posix(),
                "remote_validation_status": "VALID",
                "remote_attestation_status": "PASS",
            },
        },
    )

    view = build_evidence_view(run_id, base_dir=tmp_path)

    assert view.federated_evidence_state_summary == "INCONSISTENT"
    assert view.remote_evidence_packet_count == 2
    assert len(view.packet_list) == 2
