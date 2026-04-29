import json
from pathlib import Path

from abx.proof.artifact_writer import sha256_for_obj, write_replay_artifacts


def test_hash_determinism_and_change_detection():
    obj = {"z": [2, 1], "a": {"k": "v"}}
    same_obj = {"a": {"k": "v"}, "z": [2, 1]}
    changed = {"a": {"k": "v2"}, "z": [2, 1]}

    assert sha256_for_obj(obj) == sha256_for_obj(same_obj)
    assert sha256_for_obj(obj) != sha256_for_obj(changed)


def test_write_replay_artifacts_creates_files(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = write_replay_artifacts(
        "run-001",
        {"r": 1},
        {"a": 2},
        {"f": 3},
        {"items": []},
    )

    for key in ("calibration", "advisory", "fusion", "operator_queue"):
        path = Path(out[key]["path"])
        assert path.exists()
        assert out[key]["sha256"].startswith("sha256:")
        json.loads(path.read_text(encoding="utf-8"))
