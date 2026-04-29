from __future__ import annotations

import hashlib
import json
import os
from typing import Any


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_for_obj(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def write_json_artifact(obj: Any, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = canonical_json_bytes(obj)
    with open(path, "wb") as handle:
        handle.write(data)
    return "sha256:" + hashlib.sha256(data).hexdigest()


def write_replay_artifacts(run_id: str, report: Any, advisory: Any, fusion: Any, queue: Any) -> dict[str, dict[str, str]]:
    base = f"out/replay/artifacts/{run_id}/"
    return {
        "calibration": {
            "path": base + "calibration.json",
            "sha256": write_json_artifact(report, base + "calibration.json"),
        },
        "advisory": {
            "path": base + "advisory.json",
            "sha256": write_json_artifact(advisory, base + "advisory.json"),
        },
        "fusion": {
            "path": base + "fusion.json",
            "sha256": write_json_artifact(fusion, base + "fusion.json"),
        },
        "operator_queue": {
            "path": base + "operator_queue.json",
            "sha256": write_json_artifact(queue, base + "operator_queue.json"),
        },
    }
