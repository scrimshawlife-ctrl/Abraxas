#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from abx.mbom_v1_contracts import MBOMArtifact
from abraxas.oracle.mbom_v1 import assess_ambiguity


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MBOM v1 assessment artifact")
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    errors: list[str] = []
    parsed: MBOMArtifact | None = None

    artifact_path = Path(args.artifact)
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        parsed = MBOMArtifact.from_dict(payload)
        recomputed = assess_ambiguity(
            lifecycle_states=parsed.request.lifecycle_states,
            domain_signals=parsed.request.domain_signals,
            resonance_score=parsed.request.resonance_score,
        ).to_dict()
        if recomputed != parsed.assessment:
            errors.append("assessment mismatch")
    except Exception as exc:  # deterministic capture
        errors.append(str(exc))

    result = {
        "timestamp": utc_now(),
        "label": "mbom_v1_artifact_contract_validation",
        "artifactPath": str(artifact_path),
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "assessmentId": parsed.assessment_id if parsed else None,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    if errors:
        print(f"BLOCKED: wrote invalidation artifact to {out_path}")
        return 1

    print(f"PASS: wrote validation artifact to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
