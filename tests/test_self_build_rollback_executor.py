from __future__ import annotations

import json
from pathlib import Path

from abraxas.registry.self_build_mutation_ledger import append_mutation_entry, build_mutation_entry, snapshot_before_content
from abraxas.registry.self_build_rollback_executor import run_self_build_rollback_executor


def test_rollback_executor_happy_path() -> None:
    target = Path("out/test/rollback_target.latest.json")
    ledger = Path("out/registry/self_build_mutation_ledger.latest.json")
    # clean state
    for p in [target, ledger]:
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            p.unlink()
    # also clean any snapshot for this content (id based on before)
    before_content = '{"status":"NOT_COMPUTABLE"}'
    snap_id = __import__("hashlib").sha256(before_content.encode("utf-8")).hexdigest()
    snap = Path(f"out/registry/snapshots/{snap_id}.json")
    if snap.exists():
        snap.unlink()

    target.write_text(before_content, encoding="utf-8")

    before_hash = __import__("hashlib").sha256(before_content.encode("utf-8")).hexdigest()
    after_content = '{"status":"COMPUTABLE"}'
    target.write_text(after_content, encoding="utf-8")
    after_hash = __import__("hashlib").sha256(after_content.encode("utf-8")).hexdigest()

    snapshot = snapshot_before_content(before_content)
    entry = build_mutation_entry(
        approval_id="approval-rollback-test",
        target_path=str(target),
        before_hash=before_hash,
        after_hash=after_hash,
        before_snapshot=snapshot,
        post_validation={"validator": "PASS", "operator_card": "GREEN", "invariance": True},
    )
    append_mutation_entry(entry)

    result = run_self_build_rollback_executor(entry["mutation_id"], operator_approved=True)
    assert result["status"] == "ROLLED_BACK"
    restored = json.loads(target.read_text(encoding="utf-8"))
    assert restored["status"] == "NOT_COMPUTABLE"
