"""
Component Score Ledger
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.provenance import hash_canonical_json


class ComponentScoreLedger:
    """
    Append-only hash-chained ledger for component scores.
    """

    def __init__(
        self,
        ledger_path: str | Path = "out/score_ledgers/component_scores.jsonl",
    ):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def append_score(
        self,
        run_id: str,
        component_id: str,
        horizon: str,
        summary: Dict[str, Any],
    ) -> str:
        prev_hash = self._get_last_hash()

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "component_score",
            "run_id": run_id,
            "component_id": component_id,
            "horizon": horizon,
            "n": summary.get("n"),
            "hit_rate": summary.get("hit_rate"),
            "brier_avg": summary.get("brier_avg"),
            "coverage_rate": summary.get("coverage_rate"),
            "trend_acc": summary.get("trend_acc"),
            "abstain_rate": summary.get("abstain_rate"),
            "unknown_rate": summary.get("unknown_rate"),
            "prev_hash": prev_hash,
        }

        step_hash = hash_canonical_json(entry)
        entry["step_hash"] = step_hash

        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

        return step_hash

    def _get_last_hash(self) -> str:
        if not self.ledger_path.exists():
            return "genesis"

        with open(self.ledger_path, "r") as f:
            lines = f.readlines()
            if not lines:
                return "genesis"

            last_entry = json.loads(lines[-1])
            return last_entry.get("step_hash", "genesis")


def write_component_score_summary(
    run_id: str,
    summary: Dict[str, Any],
    output_dir: str | Path = "out",
) -> None:
    output_dir = Path(output_dir)
    runs_dir = output_dir / "runs" / run_id / "scoreboard"
    runs_dir.mkdir(parents=True, exist_ok=True)

    json_path = runs_dir / "component_score_summary.json"
    md_path = runs_dir / "component_score_summary.md"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    md_path.write_text(_render_summary_md(summary))


def _render_summary_md(summary: Dict[str, Any]) -> str:
    lines = ["# Component Score Summary", ""]
    for component_id in sorted(summary.keys()):
        data = summary[component_id]
        lines.extend(
            [
                f"## {component_id}",
                f"- n: {data.get('n')}",
                f"- hit_rate: {data.get('hit_rate')}",
                f"- brier_avg: {data.get('brier_avg')}",
                f"- coverage_rate: {data.get('coverage_rate')}",
                f"- trend_acc: {data.get('trend_acc')}",
                f"- abstain_rate: {data.get('abstain_rate')}",
                f"- unknown_rate: {data.get('unknown_rate')}",
                "",
            ]
        )
    return "\n".join(lines)
