from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
import zipfile
from typing import Any, Dict, List, Tuple


def canonical_json_bytes(obj: Any) -> bytes:
    rendered = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return rendered.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ledger_payload(ledger_store, run_id: str) -> Dict[str, Any]:
    events = ledger_store.list_events(run_id)
    return {
        "run_id": run_id,
        "chain_valid": ledger_store.chain_valid(run_id),
        "events": [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp_utc": event.timestamp_utc,
                "prev_event_hash": event.prev_event_hash,
                "event_hash": event.event_hash,
                "data": event.data,
            }
            for event in events
        ],
    }


def build_bundle(
    *,
    left_run,
    right_run,
    compare_summary: Dict[str, Any],
    policy_snapshot: Dict[str, Any],
    ledger_store,
) -> bytes:
    files: List[Tuple[str, bytes]] = []

    files.append(("left.packet.json", canonical_json_bytes(left_run.signal.model_dump())))
    files.append(("left.ledger.json", canonical_json_bytes(_ledger_payload(ledger_store, left_run.run_id))))
    files.append(("right.packet.json", canonical_json_bytes(right_run.signal.model_dump())))
    files.append(("right.ledger.json", canonical_json_bytes(_ledger_payload(ledger_store, right_run.run_id))))
    files.append(("compare.json", canonical_json_bytes(compare_summary)))
    files.append(("policy.json", canonical_json_bytes(policy_snapshot)))
    if left_run.stability_report:
        files.append(("stability.left.json", canonical_json_bytes(left_run.stability_report)))
    if right_run.stability_report:
        files.append(("stability.right.json", canonical_json_bytes(right_run.stability_report)))

    manifest_files = []
    for name, data in files:
        manifest_files.append(
            {"name": name, "sha256": sha256_hex(data), "bytes": len(data)}
        )

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "left_run_id": left_run.run_id,
        "right_run_id": right_run.run_id,
        "files": manifest_files,
    }
    files.append(("manifest.json", canonical_json_bytes(manifest)))

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_STORED) as bundle:
        for name, data in files:
            bundle.writestr(name, data)
    return buffer.getvalue()
