from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from abx.federated_transport import verify_remote_evidence_manifest


def test_remote_evidence_manifest_not_declared() -> None:
    result = verify_remote_evidence_manifest(None)
    assert result.status.value == "NOT_DECLARED"


def test_remote_evidence_manifest_missing(tmp_path: Path) -> None:
    result = verify_remote_evidence_manifest("out/federated/missing.json", base_dir=tmp_path)
    assert result.status.value == "MISSING"
    assert "remote_evidence_manifest_missing" in result.errors


def test_remote_evidence_manifest_malformed_v1(tmp_path: Path) -> None:
    manifest = tmp_path / "out" / "federated" / "bad.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"schema": "RemoteEvidenceManifest.v1", "packets": []}), encoding="utf-8")

    result = verify_remote_evidence_manifest(manifest.relative_to(tmp_path).as_posix(), base_dir=tmp_path)
    assert result.status.value == "MALFORMED"
    assert "remote_evidence_manifest_run_id_missing" in result.errors


def test_remote_evidence_manifest_valid_v1(tmp_path: Path) -> None:
    manifest = tmp_path / "out" / "federated" / "good.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "schema": "RemoteEvidenceManifest.v1",
                "manifest_id": "manifest-1",
                "run_id": "RUN-1",
                "origin": "FEDERATION://cluster-a",
                "packets": [
                    {
                        "packet_id": "pkt-1",
                        "run_id": "RUN-1",
                        "ref": "remote://packet/1",
                        "status": "VALID",
                        "observed_at": "2026-03-30T00:00:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = verify_remote_evidence_manifest(
        manifest.relative_to(tmp_path).as_posix(),
        base_dir=tmp_path,
        now=datetime(2026, 3, 30, tzinfo=timezone.utc),
    )
    assert result.status.value == "VALID"
    assert result.manifest_id == "manifest-1"
    assert result.origin == "federation://cluster-a"
    assert result.packet_ids == ["pkt-1"]


def test_remote_evidence_manifest_detects_inconsistent_packets(tmp_path: Path) -> None:
    manifest = tmp_path / "out" / "federated" / "inconsistent.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "schema": "RemoteEvidenceManifest.v1",
                "manifest_id": "manifest-i",
                "run_id": "RUN-I",
                "origin": "federation://cluster-a",
                "packets": [
                    {
                        "packet_id": "pkt-ok",
                        "run_id": "RUN-I",
                        "ref": "remote://packet/ok",
                        "status": "VALID",
                        "observed_at": "2026-03-30T00:00:00+00:00",
                    },
                    {
                        "packet_id": "pkt-bad",
                        "run_id": "RUN-I",
                        "ref": "remote://packet/bad",
                        "status": "FAIL",
                        "observed_at": "2026-03-30T00:00:00+00:00",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = verify_remote_evidence_manifest(
        manifest.relative_to(tmp_path).as_posix(),
        base_dir=tmp_path,
        now=datetime(2026, 3, 30, tzinfo=timezone.utc),
    )
    assert result.status.value == "INCONSISTENT"
    assert result.inconsistent is True


def test_remote_evidence_manifest_detects_stale(tmp_path: Path) -> None:
    manifest = tmp_path / "out" / "federated" / "stale.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "schema": "RemoteEvidenceManifest.v1",
                "manifest_id": "manifest-s",
                "run_id": "RUN-S",
                "origin": "federation://cluster-a",
                "packets": [
                    {
                        "packet_id": "pkt-1",
                        "run_id": "RUN-S",
                        "ref": "remote://packet/1",
                        "status": "VALID",
                        "observed_at": "2026-03-01T00:00:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = verify_remote_evidence_manifest(
        manifest.relative_to(tmp_path).as_posix(),
        base_dir=tmp_path,
        now=datetime(2026, 3, 30, tzinfo=timezone.utc),
    )
    assert result.status.value == "STALE"
    assert result.stale_packet_count == 1
