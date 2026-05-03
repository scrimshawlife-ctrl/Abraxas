from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from abraxas.registry.self_build_recommendation_execution_ledger import append_execution_entry
from abraxas.registry.self_build_recommendation_executor import run_self_build_recommendation_executor


def main() -> None:
    action_id = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_self_build_recommendation_executor(action_id=action_id)
    ledger = append_execution_entry(result)
    out_path = Path("out/registry/self_build_recommendation_execution_ledger.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ledger, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
