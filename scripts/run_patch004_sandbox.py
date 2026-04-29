from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

from abx.repair.noop_executor import run_noop_executor
from abx.repair.planner import build_repair_manifest
from abx.repair.receipt_binding import write_patch004_binding_artifacts


def _default_summary() -> Dict[str, Any]:
    return {
        "readiness_status": "READY_FOR_DESIGN",
        "design_pass_allowed": True,
        "execution_allowed": False,
        "runtime_mutation_allowed": False,
        "execution_triggered": False,
        "runtime_mutation": False,
        "authority_leak_detected": False,
        "cycle_count_observed": 30,
    }


def main(argv: list[str]) -> int:
    summary = _default_summary()
    write_binding = "--write-binding" in argv[1:]
    path_args = [a for a in argv[1:] if a != "--write-binding"]
    if path_args:
        summary = json.loads(Path(path_args[0]).read_text(encoding="utf-8"))
    manifest = build_repair_manifest(summary)
    receipt = run_noop_executor(manifest)
    if write_binding:
        meta = write_patch004_binding_artifacts(str(receipt.get("run_id", "NOT_COMPUTABLE")), manifest, receipt)
        print(json.dumps({"receipt": receipt, "binding": meta["binding"]}, indent=2, sort_keys=True))
    else:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
