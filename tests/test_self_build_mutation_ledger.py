from __future__ import annotations

import json
from pathlib import Path

from abraxas.registry.self_build_mutation_ledger import (
    append_mutation_entry,
    build_mutation_entry,
    snapshot_before_content,
)


def test_mutation_ledger_snapshot_pointer() -> None:
    before_content = '{"schema_version":"Test.v1","status":"NOT_COMPUTABLE"}'
    before_snapshot = snapshot_before_content(before_content)
    entry = build_mutation_entry(
        approval_id="approval-test",
        target_path="out/test/test.latest.json",
        before_hash="before-hash",
        after_hash="after-hash",
        before_snapshot=before_snapshot,
        post_validation={"validator": "PASS", "operator_card": "GREEN", "invariance": True},
    )
    payload = append_mutation_entry(entry)
    assert payload["schema_version"] == "SelfBuildMutationLedgerCollection.v1"

    latest = payload["entries"][-1]
    assert latest["rollback_ready"] is True
    assert latest["before_snapshot"]["storage"] == "POINTER"
    snapshot_path = Path(latest["before_snapshot"]["payload_or_ref"])
    assert snapshot_path.exists()

    ledger_path = Path("out/registry/self_build_mutation_ledger.latest.json")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["entry_count"] >= 1
