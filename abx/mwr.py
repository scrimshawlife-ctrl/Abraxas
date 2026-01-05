from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from abraxas.evolve.non_truncation import enforce_non_truncation
from abraxas.memetic.dmx import compute_dmx
from abraxas.memetic.extract import build_mimetic_weather, extract_terms, read_oracle_texts
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Abraxas MWR/A2 v0.1 (mimetic weather + AAlmanac slang emergence)"
    )
    p.add_argument("--run-id", required=True)
    p.add_argument(
        "--oracle-paths",
        nargs="+",
        required=True,
        help="One or more oracle run files (json/jsonl/md)",
    )
    p.add_argument("--out-dir", default="out/reports")
    p.add_argument("--max-terms", type=int, default=60)
    p.add_argument("--value-ledger", default="out/value_ledgers/mwr_runs.jsonl")
    args = p.parse_args()

    ts = _utc_now_iso()
    docs: List[tuple[str, str]] = []
    for path in args.oracle_paths:
        docs.extend(read_oracle_texts(path))

    terms = extract_terms(docs, max_terms=int(args.max_terms))
    units = build_mimetic_weather(args.run_id, terms, ts=ts)
    dmx = compute_dmx(
        sources=[],
        signals=_extract_disinfo_signals(units),
    ).to_dict()

    a2 = {
        "version": "a2_terms.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "terms": [t.to_dict() for t in terms],
        "dmx": dmx,
        "provenance": {"oracle_paths": list(args.oracle_paths)},
    }
    a2 = enforce_non_truncation(
        artifact=a2,
        raw_full={"terms": [t.to_dict() for t in terms]},
    )
    a2["views"] = {"top_terms": [t.to_dict() for t in terms[:25]]}
    a2_json = os.path.join(args.out_dir, f"a2_{args.run_id}.json")
    a2_md = os.path.join(args.out_dir, f"a2_{args.run_id}.md")
    _write_json(a2_json, a2)
    os.makedirs(os.path.dirname(a2_md), exist_ok=True)
    with open(a2_md, "w", encoding="utf-8") as f:
        f.write("# AAlmanac / Slang Emergence (A2) v0.1\n\n")
        f.write(f"- run_id: `{args.run_id}`\n- ts: `{ts}`\n\n")
        f.write("## Top term candidates\n")
        for term in terms[:25]:
            f.write(
                f"- **{term.term}** count={term.count} vel/day={term.velocity_per_day:.2f} "
                f"novelty={term.novelty_score:.2f} prop={term.propagation_score:.2f} "
                f"risk={term.manipulation_risk:.2f} tags={term.tags}\n"
            )

    mwr = {
        "version": "mimetic_weather.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "units": [u.to_dict() for u in units],
        "dmx": dmx,
        "provenance": {"oracle_paths": list(args.oracle_paths), "a2_terms": a2_json},
    }
    mwr = enforce_non_truncation(
        artifact=mwr,
        raw_full={"units": [u.to_dict() for u in units]},
    )
    mwr["views"] = {
        "top_units": [u.to_dict() for u in units[:8]],
    }
    mwr_json = os.path.join(args.out_dir, f"mwr_{args.run_id}.json")
    mwr_md = os.path.join(args.out_dir, f"mwr_{args.run_id}.md")
    _write_json(mwr_json, mwr)
    with open(mwr_md, "w", encoding="utf-8") as f:
        f.write("# Mimetic Weather Report (MWR) v0.1\n\n")
        f.write(f"- run_id: `{args.run_id}`\n- ts: `{ts}`\n\n")
        f.write("## Weather fronts\n")
        for unit in units:
            f.write(
                f"- **{unit.label}** intensity={unit.intensity:.2f} dir={unit.direction} "
                f"conf={unit.confidence:.2f} horizon={unit.horizon_tags} "
                f"disinfo={unit.disinfo_metrics}\n"
            )
            if unit.supporting_terms:
                f.write(f"  - terms: {', '.join(unit.supporting_terms[:12])}\n")

    # Use capability contract for ledger append
    ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.mwr", git_hash="unknown")
    invoke_capability(
        "evolve.ledger.append",
        {
            "path": args.value_ledger,
            "record": {
                "run_id": args.run_id,
                "mwr_json": mwr_json,
                "a2_json": a2_json,
                "oracle_paths": list(args.oracle_paths),
            }
        },
        ctx=ctx,
        strict_execution=True
    )
    print(f"[A2] wrote: {a2_json}")
    print(f"[A2] wrote: {a2_md}")
    print(f"[MWR] wrote: {mwr_json}")
    print(f"[MWR] wrote: {mwr_md}")
    return 0


def _extract_disinfo_signals(units: List[Any]) -> Dict[str, Any]:
    disinfo_unit = None
    for unit in units:
        if getattr(unit, "label", None) == "disinfo_fog":
            disinfo_unit = unit
            break
    if not disinfo_unit:
        return {"ai_markers": 0.0, "bot_markers": 0.0, "incentive_markers": 0.0, "forensics_flags": 0}
    metrics = getattr(disinfo_unit, "disinfo_metrics", {}) or {}
    ai_markers = float(metrics.get("deepfake_pollution_risk") or 0.0)
    bot_markers = float(metrics.get("manipulation_risk_mean") or 0.0)
    return {
        "ai_markers": ai_markers,
        "bot_markers": bot_markers,
        "incentive_markers": 0.0,
        "forensics_flags": 0,
    }


if __name__ == "__main__":
    raise SystemExit(main())
