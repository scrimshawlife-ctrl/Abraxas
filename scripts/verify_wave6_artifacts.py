#!/usr/bin/env python3
"""Verify Wave 6 artifact consistency across stub index, taxonomy, and notion sync outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to parse json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"invalid json root (expected object): {path}")
    return payload


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def verify(*, stub_index: dict[str, Any], taxonomy: dict[str, Any], notion_sync: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []

    stub_summary = stub_index.get("summary") if isinstance(stub_index.get("summary"), dict) else {}
    taxonomy_summary = taxonomy.get("gap_summary") if isinstance(taxonomy.get("gap_summary"), dict) else {}
    sync_metrics = notion_sync.get("metrics") if isinstance(notion_sync.get("metrics"), dict) else {}

    total_stubs = _as_int(stub_summary.get("total_stubs"))
    impl_gap = _as_int(taxonomy_summary.get("implementation_gap"))
    policy_block = _as_int(taxonomy_summary.get("policy_block"))
    intentional_abstract = _as_int(taxonomy_summary.get("intentional_abstract"))

    if _as_int(sync_metrics.get("total_stubs")) != total_stubs:
        errors.append("metrics.total_stubs mismatch")
    if _as_int(sync_metrics.get("implementation_gap")) != impl_gap:
        errors.append("metrics.implementation_gap mismatch")
    if _as_int(sync_metrics.get("policy_block")) != policy_block:
        errors.append("metrics.policy_block mismatch")
    if _as_int(sync_metrics.get("intentional_abstract")) != intentional_abstract:
        errors.append("metrics.intentional_abstract mismatch")

    tasks = notion_sync.get("tasks") if isinstance(notion_sync.get("tasks"), list) else []
    task_ids = {t.get("id") for t in tasks if isinstance(t, dict)}
    required_ids = {"operator_gap_burn_down", "policy_guardrails", "intentional_abstract_inventory"}
    missing = sorted(required_ids - task_ids)
    if missing:
        errors.append("missing tasks: " + ", ".join(missing))

    status = notion_sync.get("status") if isinstance(notion_sync.get("status"), dict) else {}
    if status.get("evidence_backed") is not True:
        errors.append("status.evidence_backed must be true")

    return (len(errors) == 0), errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Wave 6 artifact consistency")
    parser.add_argument("--stub-index", default="tools/stub_index.json")
    parser.add_argument("--taxonomy", default="docs/artifacts/notion_stub_taxonomy.json")
    parser.add_argument("--sync", default="docs/artifacts/notion_sync_status.json")
    args = parser.parse_args()

    stub_index = _read_json(Path(args.stub_index))
    taxonomy = _read_json(Path(args.taxonomy))
    notion_sync = _read_json(Path(args.sync))

    ok, errors = verify(stub_index=stub_index, taxonomy=taxonomy, notion_sync=notion_sync)
    if not ok:
        print("[WAVE6_VERIFY] FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("[WAVE6_VERIFY] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
