from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json

from aatf.ingest.loaders import load_json_payload
from aatf.queue.review import enqueue_review
from aatf.export.aalmanac import export_aalmanac_bundle
from aatf.provenance import deterministic_hash
from aatf.storage import local_ledger_path


def ingest_payload(path: str) -> Dict[str, Any]:
    payload = load_json_payload(path)
    record = {
        "schema_version": "aatf.ingest.v0",
        "payload_path": path,
        "payload_hash": deterministic_hash(payload),
        "payload": payload,
    }
    ledger = local_ledger_path("ingest")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    enqueue_review(record)
    return record


def export_bundle(output_dir: str) -> Dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    bundle = {
        "aalmanac": export_aalmanac_bundle(out),
    }
    manifest = out / "bundle_manifest.json"
    manifest.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    return bundle
