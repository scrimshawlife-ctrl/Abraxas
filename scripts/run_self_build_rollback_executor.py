from __future__ import annotations

import json
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from abraxas.registry.self_build_rollback_executor import run_self_build_rollback_executor


def main() -> None:
    mutation_id = os.environ.get("MUTATION_ID", "")
    approved = os.environ.get("OPERATOR_APPROVED", "false").lower() == "true"
    result = run_self_build_rollback_executor(mutation_id, approved)
    out_path = Path("out/registry/self_build_rollback_result.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
