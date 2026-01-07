from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

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
    docs: List[Dict[str, str]] = []
    for path in args.oracle_paths:
        ctx = RuneInvocationContext(
            run_id=args.run_id,
            subsystem_id="abx.mwr",
            git_hash="unknown"
        )
        result = invoke_capability(
            "memetic.oracle_texts.read",
            {"path": path},
            ctx=ctx,
            strict_execution=True
        )
        docs.extend(result.get("docs", []))

    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.mwr",
        git_hash="unknown"
    )
    terms_result = invoke_capability(
        "memetic.terms.extract",
        {"docs": docs, "max_terms": int(args.max_terms)},
        ctx=ctx,
        strict_execution=True
    )
    terms = terms_result.get("terms", [])
    units_result = invoke_capability(
        "memetic.weather.build",
        {"run_id": args.run_id, "terms": terms, "ts": ts},
        ctx=ctx,
        strict_execution=True
    )
    units = units_result.get("units", [])
    dmx_result = invoke_capability(
        "memetic.dmx.compute",
        {"sources": [], "signals": _extract_disinfo_signals(units)},
        ctx=ctx,
        strict_execution=True
    )
    dmx = dmx_result.get("dmx", {})

    a2 = {
        "version": "a2_terms.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "terms": list(terms),
        "dmx": dmx,
        "provenance": {"oracle_paths": list(args.oracle_paths)},
    }

    # Enforce non-truncation policy for a2 artifact
    ctx_a2 = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.mwr",
        git_hash="unknown"
    )
    result_a2 = invoke_capability(
        capability="evolve.policy.enforce_non_truncation",
        inputs={
            "artifact": a2,
            "raw_full": {"terms": list(terms)}
        },
        ctx=ctx_a2,
        strict_execution=True
    )
    a2 = result_a2["artifact"]

    a2["views"] = {"top_terms": list(terms[:25])}
    a2_json = os.path.join(args.out_dir, f"a2_{args.run_id}.json")
    a2_md = os.path.join(args.out_dir, f"a2_{args.run_id}.md")
    _write_json(a2_json, a2)
    os.makedirs(os.path.dirname(a2_md), exist_ok=True)
    with open(a2_md, "w", encoding="utf-8") as f:
        f.write("# AAlmanac / Slang Emergence (A2) v0.1\n\n")
        f.write(f"- run_id: `{args.run_id}`\n- ts: `{ts}`\n\n")
        f.write("## Top term candidates\n")
        for term in terms[:25]:
            velocity = float(term.get("velocity_per_day") or 0.0)
            novelty = float(term.get("novelty_score") or 0.0)
            propagation = float(term.get("propagation_score") or 0.0)
            risk = float(term.get("manipulation_risk") or 0.0)
            f.write(
                f"- **{term.get('term')}** count={term.get('count')} vel/day={velocity:.2f} "
                f"novelty={novelty:.2f} prop={propagation:.2f} "
                f"risk={risk:.2f} tags={term.get('tags')}\n"
            )

    mwr = {
        "version": "mimetic_weather.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "units": list(units),
        "dmx": dmx,
        "provenance": {"oracle_paths": list(args.oracle_paths), "a2_terms": a2_json},
    }

    # Enforce non-truncation policy for mwr artifact
    ctx_mwr = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.mwr",
        git_hash="unknown"
    )
    result_mwr = invoke_capability(
        capability="evolve.policy.enforce_non_truncation",
        inputs={
            "artifact": mwr,
            "raw_full": {"units": list(units)}
        },
        ctx=ctx_mwr,
        strict_execution=True
    )
    mwr = result_mwr["artifact"]

    mwr["views"] = {
        "top_units": list(units[:8]),
    }
    mwr_json = os.path.join(args.out_dir, f"mwr_{args.run_id}.json")
    mwr_md = os.path.join(args.out_dir, f"mwr_{args.run_id}.md")
    _write_json(mwr_json, mwr)
    with open(mwr_md, "w", encoding="utf-8") as f:
        f.write("# Mimetic Weather Report (MWR) v0.1\n\n")
        f.write(f"- run_id: `{args.run_id}`\n- ts: `{ts}`\n\n")
        f.write("## Weather fronts\n")
        for unit in units:
            intensity = float(unit.get("intensity") or 0.0)
            confidence = float(unit.get("confidence") or 0.0)
            f.write(
                f"- **{unit.get('label')}** intensity={intensity:.2f} dir={unit.get('direction')} "
                f"conf={confidence:.2f} horizon={unit.get('horizon_tags')} "
                f"disinfo={unit.get('disinfo_metrics')}\n"
            )
            supporting_terms = unit.get("supporting_terms") or []
            if supporting_terms:
                f.write(f"  - terms: {', '.join(supporting_terms[:12])}\n")

    # Append to value ledger via capability contract
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.mwr",
        git_hash="unknown"
    )
    invoke_capability(
        capability="evolve.ledger.append",
        inputs={
            "ledger_path": args.value_ledger,
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
        if (unit.get("label") if isinstance(unit, dict) else None) == "disinfo_fog":
            disinfo_unit = unit
            break
    if not disinfo_unit:
        return {"ai_markers": 0.0, "bot_markers": 0.0, "incentive_markers": 0.0, "forensics_flags": 0}
    metrics = disinfo_unit.get("disinfo_metrics", {}) if isinstance(disinfo_unit, dict) else {}
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
