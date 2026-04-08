#!/usr/bin/env python3
import json
from pathlib import Path
from _common import parser_base
import subprocess, sys

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


def _resolve_ledger(ledger: str) -> Path:
    return LEDGER_MAP.get(ledger, Path(ledger))


def main() -> int:
    p = parser_base("Append governance record")
    p.add_argument("--record", help="Record path (legacy flag)")
    p.add_argument("--record-file", help="Record path")
    p.add_argument("--ledger", required=True, help="Ledger name or explicit path")
    a = p.parse_args()

    record_path = _resolve_record_path(a.record, a.record_file)
    ledger_path = _resolve_ledger(a.ledger)

    rc = subprocess.call([
        sys.executable,
        str(Path(__file__).with_name("validate_governance_record.py")),
        "--record-file",
        str(record_path),
        "--ledger",
        a.ledger,
    ])
    if rc != 0:
        print("REJECTED")
        return 1

    rec = json.loads(record_path.read_text())
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    print("APPENDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
