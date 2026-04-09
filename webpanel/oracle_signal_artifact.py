from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def resolve_oracle_signal_artifact_path(raw_path: str) -> Path:
    root = Path("out/oracle_signal_layer_v2").resolve()
    candidate = Path(raw_path).expanduser().resolve()
    if root not in candidate.parents and candidate != root:
        raise ValueError("artifact path must be under out/oracle_signal_layer_v2")
    if not candidate.exists():
        raise FileNotFoundError("artifact not found")
    return candidate


def load_oracle_signal_artifact(raw_path: str) -> dict[str, Any]:
    artifact_path = resolve_oracle_signal_artifact_path(raw_path)
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    return {
        "artifact_path": str(artifact_path),
        "payload": payload if isinstance(payload, dict) else {},
        "authority": payload.get("authority") if isinstance(payload, dict) and isinstance(payload.get("authority"), dict) else {},
        "advisory_attachments": payload.get("advisory_attachments") if isinstance(payload, dict) and isinstance(payload.get("advisory_attachments"), list) else [],
    }
