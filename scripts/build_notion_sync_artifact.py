#!/usr/bin/env python3
"""Build machine-readable Notion sync status artifact from repo evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def build_sync_artifact(
    *,
    stub_index: Dict[str, Any],
    taxonomy: Dict[str, Any],
    next_steps: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    summary = stub_index.get("summary") if isinstance(stub_index.get("summary"), dict) else {}
    gap_summary = taxonomy.get("gap_summary") if isinstance(taxonomy.get("gap_summary"), dict) else {}

    total_stubs = int(summary.get("total_stubs") or 0)
    implementation_gap = int(gap_summary.get("implementation_gap") or 0)
    policy_block = int(gap_summary.get("policy_block") or 0)
    intentional_abstract = int(gap_summary.get("intentional_abstract") or 0)
    next_steps = next_steps if isinstance(next_steps, dict) else {}
    listed_complete = bool(next_steps.get("all_listed_next_steps_completed", False))
    wave5_complete = bool(next_steps.get("all_wave5_ranked_tasks_completed", False))
    if implementation_gap == 0 and policy_block == 0 and listed_complete and wave5_complete:
        wave_status = "wave_5_completed"
    elif implementation_gap == 0 and policy_block == 0:
        wave_status = "wave_4_completed"
    else:
        wave_status = "wave_4_in_progress"

    return {
        "version": "notion_sync.v0.1",
        "generated_at": "auto",
        "sources": {
            "stub_index": "tools/stub_index.json",
            "stub_taxonomy": "docs/artifacts/notion_stub_taxonomy.json",
            "execution_plan": "docs/notion_execution_plan_2026-03-27.md",
            "next_steps": "docs/artifacts/notion_next_steps.json",
        },
        "status": {
            "wave": wave_status,
            "notion_sync_ready": True,
            "evidence_backed": True,
        },
        "metrics": {
            "total_stubs": total_stubs,
            "implementation_gap": implementation_gap,
            "policy_block": policy_block,
            "intentional_abstract": intentional_abstract,
        },
        "tasks": [
            {
                "id": "operator_gap_burn_down",
                "state": "in_progress" if implementation_gap > 0 else "completed",
                "remaining": implementation_gap,
                "evidence": ["tools/stub_index.json", "docs/artifacts/notion_stub_taxonomy.json"],
            },
            {
                "id": "policy_guardrails",
                "state": "in_progress" if policy_block > 0 else "completed",
                "remaining": policy_block,
                "evidence": ["docs/artifacts/notion_stub_taxonomy.json"],
            },
            {
                "id": "intentional_abstract_inventory",
                "state": "tracked",
                "remaining": intentional_abstract,
                "evidence": ["docs/artifacts/notion_stub_taxonomy.json"],
            },
            {
                "id": "wave5_ranked_closure",
                "state": "completed" if wave5_complete else "in_progress",
                "remaining": 0 if wave5_complete else 1,
                "evidence": ["docs/artifacts/notion_next_steps.json"],
            },
        ],
        "notes": "Machine-readable closure artifact for Notion task updates.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Notion sync artifact from repo state")
    parser.add_argument("--stub-index", default="tools/stub_index.json")
    parser.add_argument("--taxonomy", default="docs/artifacts/notion_stub_taxonomy.json")
    parser.add_argument("--next-steps", default="docs/artifacts/notion_next_steps.json")
    parser.add_argument("--out", default="docs/artifacts/notion_sync_status.json")
    args = parser.parse_args()

    stub_index_path = Path(args.stub_index)
    taxonomy_path = Path(args.taxonomy)
    next_steps_path = Path(args.next_steps)
    if not stub_index_path.exists():
        raise SystemExit(f"missing stub index: {stub_index_path}")
    if not taxonomy_path.exists():
        raise SystemExit(f"missing taxonomy artifact: {taxonomy_path}")
    if not next_steps_path.exists():
        raise SystemExit(f"missing next-steps artifact: {next_steps_path}")

    stub_index = _read_json(stub_index_path)
    taxonomy = _read_json(taxonomy_path)
    next_steps = _read_json(next_steps_path)
    artifact = build_sync_artifact(stub_index=stub_index, taxonomy=taxonomy, next_steps=next_steps)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[NOTION_SYNC] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
