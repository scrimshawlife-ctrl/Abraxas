import json
import os
import subprocess


def _load(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_oracle_batch_emits_packet_and_index(tmp_path):
    out_dir = tmp_path / "oracle_batch"
    payload_dir = "abraxas/oracle/fixtures/payloads"

    cmd = [
        "python",
        "-m",
        "abraxas.oracle.batch",
        "--payload-dir",
        payload_dir,
        "--out",
        str(out_dir),
        "--mode",
        "analyst",
        "--emit-signal-v2",
        "--signal-schema-check",
        "--env",
        "sandbox",
        "--seed",
        "1337",
        "--run-at",
        "2026-01-01T00:00:00Z",
        "--version",
        "2.2.0",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"oracle batch failed:\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    pkt = os.path.join(str(out_dir), "oracle_packet.json")
    idx = os.path.join(str(out_dir), "index.md")
    assert os.path.exists(pkt)
    assert os.path.exists(idx)

    obj = _load(pkt)
    assert "oracle_packet_v0_1" in obj
    assert "oracle_packet_hash" in obj
    runs = obj["oracle_packet_v0_1"]["runs"]
    assert isinstance(runs, list)
    assert len(runs) >= 2
    assert runs[0]["run_id"] == "run_01"

