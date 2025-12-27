# AAlmanac append-only event recorder (v0.1)
# Immutable time memory: JSONL append

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

DEFAULT_LOG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "aAlmanac.jsonl"
)


def _sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def record_event(
    *,
    rune_id: str,
    payload: Dict[str, Any],
    result: Any,
    provenance_bundle: Dict[str, Any],
    source: Optional[Dict[str, Any]] = None,
    log_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Append-only write. Never overwrites. No deletes. No edits.
    Returns the stored event (including id).
    """
    lp = log_path or DEFAULT_LOG_PATH
    os.makedirs(os.path.dirname(lp), exist_ok=True)

    ts = datetime.now(timezone.utc).isoformat()

    # Minimal "source" bundle; callers can pass richer info later
    src = source or {
        "source_type": "kernel.invoke",
        "source_ref": None,
        "source_sha256": _sha256_str(_stable_json(payload)),
    }

    # Event id is deterministic over (timestamp + rune + payload hash + commit) uniqueness
    # Timestamp makes it unique per call; payload hash + commit make it traceable.
    event_core = {
        "timestamp_utc": ts,
        "rune_id": rune_id,
        "payload_sha256": _sha256_str(_stable_json(payload)),
        "repo_commit": provenance_bundle.get("repo_commit", "unknown"),
    }
    almanac_event_id = _sha256_str(_stable_json(event_core))

    event = {
        "almanac_event_id": almanac_event_id,
        "timestamp_utc": ts,
        "source": src,
        "signal": {
            "raw_text": payload.get("text_event") if isinstance(payload, dict) else None,
            "normalized_text": None,
            "language": payload.get("language") if isinstance(payload, dict) else None,
        },
        "detections": [
            {
                "rune_id": rune_id,
                "labels": payload.get("labels") if isinstance(payload, dict) else None,
                "metrics": payload.get("metrics") if isinstance(payload, dict) else None,
                "confidence": payload.get("confidence")
                if isinstance(payload, dict)
                else None,
            }
        ],
        "decay_model": payload.get("decay_model") if isinstance(payload, dict) else None,
        "provenance_bundle": provenance_bundle,
        "artifact_preview": {
            "result_type": type(result).__name__,
            "result_sha256": _sha256_str(_stable_json(result)) if result is not None else None,
        },
    }

    # JSONL append (one line per event)
    with open(lp, "a", encoding="utf-8") as file:
        file.write(_stable_json(event) + "\n")

    return event
