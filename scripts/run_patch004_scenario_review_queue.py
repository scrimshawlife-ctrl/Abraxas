from __future__ import annotations

import json
import sys
from pathlib import Path

from abx.repair.scenario_engine import run_scenario_batch
from abx.repair.scenario_review_queue import build_scenario_review_queue


def main(argv: list[str]) -> int:
    batch = None
    if len(argv) > 1:
        batch = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    if batch is None:
        batch = run_scenario_batch()
    out = build_scenario_review_queue(batch)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
