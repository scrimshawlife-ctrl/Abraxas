#!/usr/bin/env python3
import json
from pathlib import Path
from _common import parser_base

REQ = ["record_type", "timestamp", "status", "provenance", "correlation_pointers"]
ROOT = Path(__file__).resolve().parents[2]
LEDGER_MAP = {
    "promotion_decisions": ROOT / ".abraxas" / "ledger" / "promotion_decisions.jsonl",
    "revocation_events": ROOT / ".abraxas" / "ledger" / "revocation_events.jsonl",
    "release_manifests": ROOT / ".abraxas" / "ledger" / "release_manifests.jsonl",
    "audit_reports": ROOT / ".abraxas" / "ledger" / "audit_reports.jsonl",
}


def _resolve_record_path(record: str | None, record_file: str | None) -> Path:
    target = record_file or record
    if not target:
        raise ValueError("record path is required")
    return Path(target)


def main() -> int:
    p = parser_base("Validate governance record")
    p.add_argument("--record", help="Record path (legacy flag)")
    p.add_argument("--record-file", help="Record path")
    p.add_argument("--ledger", help="Optional ledger name/path for existence check")
    a = p.parse_args()

    record_path = _resolve_record_path(a.record, a.record_file)
    rec = json.loads(record_path.read_text())
    miss = [k for k in REQ if k not in rec]
    if miss:
        print(f"INVALID missing={miss}")
        return 1

    if rec.get("record_type") == "release_manifest":
        registration_receipt = rec.get("registration_receipt")
        if not isinstance(registration_receipt, dict):
            print("INVALID missing=registration_receipt")
            return 1
        if registration_receipt.get("label") != "subsystem_registration_check":
            print("INVALID registration_receipt.label")
            return 1
        if registration_receipt.get("status") not in {"PASS", "BLOCKED"}:
            print("INVALID registration_receipt.status")
            return 1

    if a.ledger:
        ledger_path = LEDGER_MAP.get(a.ledger, Path(a.ledger))
        if not ledger_path.parent.exists():
            print(f"INVALID ledger_parent_missing={ledger_path.parent}")
            return 1

    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
