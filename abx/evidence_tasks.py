from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return d if isinstance(d, dict) else {}


def main() -> int:
    p = argparse.ArgumentParser(description="Render Evidence Escalation Task Sheet (md)")
    p.add_argument("--run-id", required=True)
    p.add_argument("--out-reports", default="out/reports")
    args = p.parse_args()

    ts = _utc_now_iso()
    ap = _read_json(os.path.join(args.out_reports, f"acquisition_plan_{args.run_id}.json"))
    actions = ap.get("actions") if isinstance(ap.get("actions"), list) else []
    dmx = ap.get("dmx") if isinstance(ap.get("dmx"), dict) else {}

    by_term: Dict[str, List[Dict[str, Any]]] = {}
    for a in actions:
        if not isinstance(a, dict):
            continue
        term = str(a.get("term") or "").strip()
        if not term:
            continue
        by_term.setdefault(term, []).append(a)

    out_md = os.path.join(args.out_reports, f"evidence_tasks_{args.run_id}.md")
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Evidence Escalation Tasks\n\n")
        f.write(f"- run_id: `{args.run_id}`\n")
        f.write(f"- ts: `{ts}`\n")
        f.write(
            f"- dmx: overall={dmx.get('overall_manipulation_risk')} bucket={dmx.get('bucket')}\n\n"
        )

        for term in sorted(by_term.keys()):
            f.write(f"## {term}\n\n")
            for a in by_term[term]:
                mode = a.get("mode")
                ch = a.get("channel")
                act = a.get("action")
                rat = a.get("rationale") or []
                f.write(f"- [{mode}] {ch}: **{act}**\n")
                if act == "search":
                    q = a.get("query") or {}
                    f.write(f"  - query: `{q.get('q')}`\n")
                    if q.get("domains"):
                        f.write(f"  - domains: `{q.get('domains')}`\n")
                if act == "prompt_user_for_artifacts":
                    f.write(f"  - prompt: {a.get('prompt')}\n")
                if rat:
                    f.write(f"  - rationale: `{rat}`\n")
            f.write("\n")

    print(f"[EVIDENCE_TASKS] wrote: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
