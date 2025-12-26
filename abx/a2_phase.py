from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any

from abraxas.evolve.non_truncation import enforce_non_truncation
from abraxas.memetic.temporal import build_temporal_profiles
from abraxas.evolve.ledger import append_chained_jsonl


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> int:
    p = argparse.ArgumentParser(description="A2 Phase/Temporal Profiles v0.1")
    p.add_argument("--run-id", required=True)
    p.add_argument("--registry", default="out/a2_registry/terms.jsonl")
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--max-terms", type=int, default=500)
    p.add_argument("--min-obs", type=int, default=2)
    p.add_argument("--now", default=None, help="Optional ISO now override")
    p.add_argument("--value-ledger", default="out/value_ledgers/a2_phase_runs.jsonl")
    args = p.parse_args()

    ts = _utc_now_iso()
    profiles_full = build_temporal_profiles(
        args.registry,
        now_iso=args.now,
        max_terms=2000000,
        min_obs=int(args.min_obs),
    )
    profiles_view = profiles_full[: int(args.max_terms)]

    out = {
        "version": "a2_phase.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "registry": args.registry,
        "views": {
            "profiles_top": [p.to_dict() for p in profiles_view],
            "profiles_top_n": int(args.max_terms),
        },
        "provenance": {"builder": "abx.a2_phase.v0.1"},
    }
    out = enforce_non_truncation(
        artifact=out,
        raw_full={"profiles": [p.to_dict() for p in profiles_full]},
    )
    out.setdefault("views", {})
    out["views"] = {
        "top_by_phase": {},
    }
    jpath = os.path.join(args.out_reports, f"a2_phase_{args.run_id}.json")
    mpath = os.path.join(args.out_reports, f"a2_phase_{args.run_id}.md")
    _write_json(jpath, out)

    buckets = {
        "surging": [],
        "resurgent": [],
        "emergent": [],
        "plateau": [],
        "decaying": [],
        "dormant": [],
    }
    for p0 in profiles_view:
        buckets.setdefault(p0.phase, []).append(p0)
    out["views"]["top_by_phase"] = {
        phase: [p0.to_dict() for p0 in buckets.get(phase, [])[:35]]
        for phase in [
            "surging",
            "resurgent",
            "emergent",
            "plateau",
            "decaying",
            "dormant",
        ]
    }

    with open(mpath, "w", encoding="utf-8") as f:
        f.write("# A2 Temporal Profiles v0.1\n\n")
        f.write(
            f"- run_id: `{args.run_id}`\n- ts: `{ts}`\n- registry: `{args.registry}`\n\n"
        )
        for phase in [
            "surging",
            "resurgent",
            "emergent",
            "plateau",
            "decaying",
            "dormant",
        ]:
            items = buckets.get(phase, [])
            f.write(f"## {phase} ({len(items)})\n")
            for p0 in items[:35]:
                f.write(
                    f"- **{p0.term}** v14={p0.v14:.2f} v60={p0.v60:.2f} "
                    f"hl_fit_days={p0.half_life_days_fit:.1f} rec_days={p0.recurrence_days} "
                    f"risk={p0.manipulation_risk_mean:.2f} obs={p0.obs_n}\n"
                )
            f.write("\n")

    append_chained_jsonl(
        args.value_ledger,
        {"run_id": args.run_id, "a2_phase_json": jpath, "registry": args.registry},
    )
    print(f"[A2_PHASE] wrote: {jpath}")
    print(f"[A2_PHASE] wrote: {mpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
