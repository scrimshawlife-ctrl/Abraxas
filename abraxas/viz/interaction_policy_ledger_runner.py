from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.canonical import canonical_json
from abraxas.viz.interaction_policy_ledger import build_ledger


def run(policy_path: Path, manifest_path: Path, out_path: Path, prior_path: Optional[Path] = None) -> Dict[str, Any]:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prior = None
    if prior_path is not None:
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
    result = build_ledger(policy, manifest, prior)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(canonical_json(result), encoding="utf-8")
    return result
