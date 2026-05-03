from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.registry.readiness_policy_ledger import append_readiness_policy_ledger


if __name__ == "__main__":
    out = append_readiness_policy_ledger()
    p = Path("out/registry/readiness_policy_ledger.latest.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
