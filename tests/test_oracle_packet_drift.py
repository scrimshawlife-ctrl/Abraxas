import hashlib
import json

from abraxas.oracle.packet_drift import classify_packet_drift


def _write_packet(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def _packet_with_run(run_id: str, slice_hash: str, shadow_summary: dict | None) -> dict:
    run = {
        "run_id": run_id,
        "payload_path": "payload.json",
        "mode": "analyst",
        "domains": [],
        "subdomains": [],
        "signal_slice_hash": slice_hash,
        "artifacts": [],
    }
    if shadow_summary is not None:
        run["shadow_summary"] = shadow_summary
    payload = {
        "oracle_packet_v0_1": {
            "meta": {"version": "0.1", "env": "sandbox", "run_at": "t", "seed": "0"},
            "runs": [run],
        }
    }
    # The packet hash must be CONTENT-DERIVED. A constant placeholder made both
    # packets look identical, so classify_packet_drift short-circuited on its
    # documented "packet hash matches -> none" rule before comparing content, and
    # neither fixture could ever reach the canon / shadow_only branches.
    payload["oracle_packet_hash"] = hashlib.sha256(
        json.dumps(payload["oracle_packet_v0_1"], sort_keys=True).encode("utf-8")
    ).hexdigest()
    return payload


def test_packet_drift_classifies_shadow_only(tmp_path):
    p1 = _packet_with_run("run_01", "slice", {"present": True, "anagram_cluster_v1": {"watch_alerts_count": 0}})
    p2 = _packet_with_run("run_01", "slice", {"present": True, "anagram_cluster_v1": {"watch_alerts_count": 1}})
    f1 = tmp_path / "p1.json"
    f2 = tmp_path / "p2.json"
    _write_packet(str(f1), p1)
    _write_packet(str(f2), p2)
    status, details = classify_packet_drift(str(f1), str(f2))
    assert status == "shadow_only"
    assert details["run_ids"] == ["run_01"]


def test_packet_drift_classifies_canon(tmp_path):
    p1 = _packet_with_run("run_01", "slice_a", {"present": True})
    p2 = _packet_with_run("run_01", "slice_b", {"present": True})
    f1 = tmp_path / "p1.json"
    f2 = tmp_path / "p2.json"
    _write_packet(str(f1), p1)
    _write_packet(str(f2), p2)
    status, details = classify_packet_drift(str(f1), str(f2))
    assert status == "canon"
    assert details["run_ids"] == ["run_01"]
