#!/usr/bin/env python3
import json
from pathlib import Path
from _common import parser_base

REQ = ["record_type", "timestamp", "status", "provenance", "correlation_pointers"]
POINTER_STATE_FIELDS = {
    "correlation_pointer_state",
    "correlation_pointer_unresolved_reasons",
}
POINTER_STATES = {"present", "empty", "unresolved"}
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
    if not isinstance(rec.get("correlation_pointers"), list):
        print("INVALID correlation_pointers")
        return 1

    pointer_state_fields_present = [field for field in POINTER_STATE_FIELDS if field in rec]
    if pointer_state_fields_present and len(pointer_state_fields_present) != len(POINTER_STATE_FIELDS):
        missing_state_fields = sorted(POINTER_STATE_FIELDS - set(pointer_state_fields_present))
        print(f"INVALID missing={missing_state_fields}")
        return 1
    if pointer_state_fields_present:
        pointer_state = rec.get("correlation_pointer_state")
        unresolved = rec.get("correlation_pointer_unresolved_reasons")
        if pointer_state not in POINTER_STATES:
            print("INVALID correlation_pointer_state")
            return 1
        if not isinstance(unresolved, list):
            print("INVALID correlation_pointer_unresolved_reasons")
            return 1
        pointers = rec.get("correlation_pointers") or []
        if pointer_state == "present" and (not pointers or unresolved):
            print("INVALID correlation_pointer_state.present")
            return 1
        if pointer_state == "empty" and (pointers or unresolved):
            print("INVALID correlation_pointer_state.empty")
            return 1
        if pointer_state == "unresolved" and not unresolved:
            print("INVALID correlation_pointer_state.unresolved")
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
