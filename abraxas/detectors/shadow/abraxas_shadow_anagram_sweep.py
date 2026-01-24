from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas_ase.engine import load_items_jsonl, run_ase


@dataclass(frozen=True)
class ASEConfig:
    items_jsonl_path: str
    outdir: str
    date: str  # YYYY-MM-DD
    pfdi_state_path: Optional[str] = None


def run_shadow_ase(cfg: ASEConfig) -> Dict[str, Any]:
    """
    Shadow-lane wrapper:
    - consumes upstream JSONL feed
    - emits ASE artifacts
    - returns the daily_report payload as a dict for Oracle Signal Layer attachment
    """
    items_path = Path(cfg.items_jsonl_path)
    outdir = Path(cfg.outdir)
    pfdi_state = Path(cfg.pfdi_state_path) if cfg.pfdi_state_path else None

    items = load_items_jsonl(items_path)
    run_ase(items=items, date=cfg.date, outdir=outdir, pfdi_state_path=pfdi_state)

    report_path = outdir / "daily_report.json"
    return json.loads(report_path.read_text(encoding="utf-8"))
