#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "docs" / "notion_execution_plan_2026-03-27.md"
DEFAULT_SYNC = ROOT / "docs" / "artifacts" / "notion_sync_status.json"
DEFAULT_OUT = ROOT / "docs" / "artifacts" / "notion_next_steps.json"


def _extract_numbered_items(text: str, start_heading: str, end_heading: str) -> list[dict[str, str]]:
    pattern = re.compile(
        rf"{re.escape(start_heading)}\n(?P<body>.*?)(?:\n{re.escape(end_heading)}|\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return []
    body = match.group("body")
    items: list[dict[str, str]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not re.match(r"^\d+\.\s+\*\*.+\*\*", stripped):
            continue
        title_match = re.match(r"^(?P<rank>\d+)\.\s+\*\*(?P<title>.+?)\*\*", stripped)
        if not title_match:
            continue
        items.append(
            {
                "rank": title_match.group("rank"),
                "title": title_match.group("title"),
            }
        )
    return items


def build_next_steps(plan_path: Path, sync_path: Path) -> dict:
    plan_text = plan_path.read_text(encoding="utf-8")
    sync_payload = json.loads(sync_path.read_text(encoding="utf-8"))
    current_wave = sync_payload.get("status", {}).get("wave", "unknown")

    wave5_tasks = _extract_numbered_items(
        plan_text,
        "### Wave 5 tasks (ranked)",
        "## ALIGN — repo-vs-notion reality check",
    )
    repo_grounded_tasks = _extract_numbered_items(
        plan_text,
        "### Remaining coding tasks (repo-grounded)",
        "---",
    )
    adapters_init = (ROOT / "abraxas" / "sources" / "adapters" / "__init__.py").read_text(encoding="utf-8")
    online_sourcing = (ROOT / "abx" / "online_sourcing.py").read_text(encoding="utf-8")
    online_resolver = (ROOT / "abx" / "online_resolver.py").read_text(encoding="utf-8")
    stub_oracle_engine = (ROOT / "abraxas" / "core" / "stub_oracle_engine.py").read_text(encoding="utf-8")

    completion = {
        "kernel_stub_scope_bound_gate": (
            "ABRAXAS_ALLOW_STUB_ORACLE" in stub_oracle_engine
            and "ABRAXAS_STUB_ORACLE_SCOPE" in stub_oracle_engine
            and "_ALLOWED_STUB_SCOPES = {\"test\", \"dev\"}" in stub_oracle_engine
        ),
        "adapter_lane_closure": "CacheOnlyAdapter" not in adapters_init,
        "decodo_execution_hardening": (
            "normalize_online_capability" in online_sourcing
            and "normalize_online_capability" in online_resolver
            and "decodo_capability_missing" in online_resolver
        ),
        "rune_operator_implementation_triage": (
            int(sync_payload.get("metrics", {}).get("implementation_gap", 1)) == 0
        ),
        "notion_closure_automation": (ROOT / "scripts" / "run_notion_next_steps.py").exists(),
    }
    task_status = [
        {
            "id": "adapter_lane_closure",
            "state": "completed" if completion["adapter_lane_closure"] else "partial",
        },
        {
            "id": "decodo_execution_hardening",
            "state": "completed" if completion["decodo_execution_hardening"] else "partial",
        },
        {
            "id": "rune_operator_implementation_triage",
            "state": "completed" if completion["rune_operator_implementation_triage"] else "partial",
        },
        {
            "id": "notion_closure_automation",
            "state": "completed" if completion["notion_closure_automation"] else "partial",
        },
    ]
    all_completed = all(completion.values())
    unresolved_task_ids = [entry["id"] for entry in task_status if entry["state"] != "completed"]
    repo_task_id_map = {
        "Adapter lane closure (highest impact)": "adapter_lane_closure",
        "Decodo execution hardening": "decodo_execution_hardening",
        "Rune operator implementation triage": "rune_operator_implementation_triage",
        "Notion closure automation": "notion_closure_automation",
    }
    remaining_repo_grounded_tasks = [
        task
        for task in repo_grounded_tasks
        if repo_task_id_map.get(task.get("title", "")) in unresolved_task_ids
    ]
    completed_repo_grounded_tasks = [
        task
        for task in repo_grounded_tasks
        if repo_task_id_map.get(task.get("title", "")) not in unresolved_task_ids
    ]
    wave5_task_id_map = {
        "Kernel stub scope-bound gate (initiated this commit)": "kernel_stub_scope_bound_gate",
        "Adapter lane closure continuation": "adapter_lane_closure",
        "Decodo/source live-path hardening": "decodo_execution_hardening",
    }
    wave5_task_status = [
        {
            "id": wave5_task_id_map.get(task.get("title", ""), f"wave5_unknown_{task.get('rank', 'x')}"),
            "title": task.get("title", ""),
            "state": (
                "completed"
                if completion.get(wave5_task_id_map.get(task.get("title", ""), ""), False)
                else "partial"
            ),
        }
        for task in wave5_tasks
    ]
    remaining_wave5_task_ids = [entry["id"] for entry in wave5_task_status if entry["state"] != "completed"]
    all_wave5_completed = not remaining_wave5_task_ids

    return {
        "version": "notion_next_steps.v0.1",
        "generated_at": "auto",
        "sources": {
            "plan": str(plan_path.relative_to(ROOT)),
            "sync_status": str(sync_path.relative_to(ROOT)),
        },
        "current_wave": current_wave,
        "recommended_focus": (
            "closure_review"
            if all_completed
            else ("wave_5" if current_wave == "wave_4_completed" else "stabilize_current_wave")
        ),
        "wave_5_ranked_tasks": wave5_tasks,
        "repo_grounded_tasks": repo_grounded_tasks,
        "remaining_repo_grounded_tasks": remaining_repo_grounded_tasks,
        "completed_repo_grounded_tasks": completed_repo_grounded_tasks,
        "all_listed_next_steps_completed": all_completed,
        "task_status": task_status,
        "remaining_task_ids": unresolved_task_ids,
        "wave_5_task_status": wave5_task_status,
        "remaining_wave5_task_ids": remaining_wave5_task_ids,
        "all_wave5_ranked_tasks_completed": all_wave5_completed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit deterministic next-step artifact from Notion plan + sync status")
    parser.add_argument("--plan", default=str(DEFAULT_PLAN))
    parser.add_argument("--sync", default=str(DEFAULT_SYNC))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    payload = build_next_steps(Path(args.plan), Path(args.sync))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
