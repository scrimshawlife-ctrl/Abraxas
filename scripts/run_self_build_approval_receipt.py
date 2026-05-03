from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from abraxas.registry.self_build_approval_receipt import run_self_build_approval_receipt


def main() -> None:
    # MANUAL CONTROL POINT
    approved: list[str] = []
    rejected: list[str] = []
    result = run_self_build_approval_receipt(approved, rejected)
    out_path = Path("out/registry/self_build_approval_receipt.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
