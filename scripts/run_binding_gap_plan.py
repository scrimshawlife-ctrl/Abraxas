from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from abraxas.registry.binding_gap_plan import run_binding_gap_plan


def main() -> None:
    result = run_binding_gap_plan()
    out_path = Path("out/registry/binding_gap_plan.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
