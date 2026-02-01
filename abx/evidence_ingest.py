from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

# apply_disinfo_metrics replaced by disinfo.apply.metrics capability
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return d if isinstance(d, dict) else {}


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> int:
    p = argparse.ArgumentParser(description="Ingest an evidence bundle JSON into out/evidence_bundles/")
    p.add_argument("--bundle", required=True, help="Path to evidence bundle JSON")
    p.add_argument("--out-dir", default="out/evidence_bundles")
    args = p.parse_args()

    ts = _utc_now_iso()
    bundle = _read_json(args.bundle)
    if not bundle.get("bundle_id"):
        bundle["bundle_id"] = f"bundle_{int(datetime.now(timezone.utc).timestamp())}"
    bundle.setdefault("ingested_ts", ts)

    b_item = {
        "source_type": bundle.get("source_type"),
        "source_ref": bundle.get("source_ref"),
        "source": {
            "type": bundle.get("source_type"),
            "url": bundle.get("source_ref"),
            "domain": "",
            "author": "",
            "captured_ts": bundle.get("captured_ts"),
        },
        "media_kind": (
            "image"
            if bundle.get("source_type") == "screenshot"
            else ("pdf" if bundle.get("source_type") == "pdf" else "text")
        ),
        "context": {"dmx": {"overall_manipulation_risk": 0.0, "bucket": "UNKNOWN"}},
    }

    # Apply disinfo metrics via capability contract
    ctx = RuneInvocationContext(
        run_id=bundle.get("bundle_id", "UNKNOWN"),
        subsystem_id="abx.evidence_ingest",
        git_hash="unknown"
    )
    disinfo_result = invoke_capability(
        "disinfo.apply.metrics",
        {"item": b_item},
        ctx=ctx,
        strict_execution=True
    )
    b_item = disinfo_result["enriched_item"]
    bundle["disinfo_labels"] = b_item.get("disinfo")

    out_path = os.path.join(args.out_dir, f"{bundle['bundle_id']}.json")
    _write_json(out_path, bundle)
    print(f"[EVIDENCE_INGEST] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
