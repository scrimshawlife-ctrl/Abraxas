import json
import os

from abraxas.oracle.batch import main as batch_main


def _write_payload(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)


def test_oracle_batch_emits_packet_and_index(tmp_path):
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir()
    out_dir = tmp_path / "out"

    shadow_block = {
        "anagram_cluster_v1": {
            "shadow_anagram_cluster_v1": {
                "clusters": [],
                "global_count": 2,
                "watch_alerts": [{"token": "Signal Layer"}],
                "artifact_hash": "abc",
            }
        }
    }
    payload1 = {"shadow": shadow_block, "meta": {"id": "p1"}}
    payload2 = {"shadow": shadow_block, "meta": {"id": "p2"}}
    _write_payload(str(payload_dir / "a.json"), payload1)
    _write_payload(str(payload_dir / "b.json"), payload2)

    rc = batch_main([
        "--payload-dir", str(payload_dir),
        "--out", str(out_dir),
        "--mode", "analyst",
        "--emit-signal-v2",
        "--signal-schema-check",
        "--env", "sandbox",
        "--seed", "1337",
        "--run-at", "2026-01-01T00:00:00Z",
        "--version", "2.2.0",
    ])
    assert rc == 0

    pkt = os.path.join(out_dir, "oracle_packet.json")
    idx = os.path.join(out_dir, "index.md")
    assert os.path.exists(pkt)
    assert os.path.exists(idx)

    with open(pkt, "r", encoding="utf-8") as f:
        obj = json.load(f)
    runs = obj["oracle_packet_v0_1"]["runs"]
    assert isinstance(runs, list)
    assert len(runs) >= 2
    assert runs[0]["run_id"] == "run_01"

    for rr in runs:
        if "shadow_summary" in rr:
            assert isinstance(rr["shadow_summary"], dict)

    with open(idx, "r", encoding="utf-8") as f:
        txt = f.read()
    assert "Shadow Alerts" in txt
