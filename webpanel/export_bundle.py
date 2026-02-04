from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from webpanel.oracle_output import extract_oracle_output, oracle_hash_prefix


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
    if left_run.policy_snapshot_at_ingest:
        files.append(
            (
                "policy.left_at_ingest.json",
                canonical_json_bytes(left_run.policy_snapshot_at_ingest),
            )
        )
    if right_run.policy_snapshot_at_ingest:
        files.append(
            (
                "policy.right_at_ingest.json",
                canonical_json_bytes(right_run.policy_snapshot_at_ingest),
            )
        )

    left_oracle = extract_oracle_output(left_run)
    right_oracle = extract_oracle_output(right_run)
    left_oracle_sha: Optional[str] = None
    right_oracle_sha: Optional[str] = None
    if left_oracle:
        left_bytes = canonical_json_bytes(left_oracle)
        files.append(("oracle.left.json", left_bytes))
        left_oracle_sha = sha256_hex(left_bytes)
    if right_oracle:
        right_bytes = canonical_json_bytes(right_oracle)
        files.append(("oracle.right.json", right_bytes))
        right_oracle_sha = sha256_hex(right_bytes)

    manifest_files = []
    for name, data in files:
        manifest_files.append(
            {"name": name, "sha256": sha256_hex(data), "bytes": len(data)}
        )

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "left_run_id": left_run.run_id,
        "right_run_id": right_run.run_id,
        "left_policy_hash_at_ingest": left_run.policy_hash_at_ingest,
        "right_policy_hash_at_ingest": right_run.policy_hash_at_ingest,
        "current_policy_hash": policy_snapshot.get("policy_hash"),
        "files": manifest_files,
    }
    if left_oracle_sha:
        manifest["left_oracle_sha256"] = left_oracle_sha
        manifest["left_oracle_input_hash_prefix"] = oracle_hash_prefix(left_oracle, "input_hash")
        manifest["left_oracle_policy_hash_prefix"] = oracle_hash_prefix(left_oracle, "policy_hash")
    if right_oracle_sha:
        manifest["right_oracle_sha256"] = right_oracle_sha
        manifest["right_oracle_input_hash_prefix"] = oracle_hash_prefix(right_oracle, "input_hash")
        manifest["right_oracle_policy_hash_prefix"] = oracle_hash_prefix(right_oracle, "policy_hash")
    files.append(("manifest.json", canonical_json_bytes(manifest)))

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_STORED) as bundle:
        for name, data in files:
            bundle.writestr(name, data)
    return buffer.getvalue()
