from __future__ import annotations

import argparse
import json
import os

from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.memetic.registry import append_a2_terms_to_registry, compute_missed_terms


def _write_json(path: str, obj: object) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> int:
    p = argparse.ArgumentParser(
        description="A2 Registry v0.1 (append + missed term report)"
    )
    p.add_argument("--a2", required=True, help="Path to out/reports/a2_<run>.json")
    p.add_argument("--registry", default="out/a2_registry/terms.jsonl")
    p.add_argument("--append", action="store_true")
    p.add_argument("--missed-report", action="store_true")
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--run-id", default=None)
    p.add_argument("--resurrect-after-days", type=int, default=10)
    args = p.parse_args()

    if args.append:
        append_a2_terms_to_registry(
            a2_path=args.a2,
            registry_path=args.registry,
            source_run_id=args.run_id,
        )

    if args.missed_report:
        rep = compute_missed_terms(
            a2_path=args.a2,
            registry_path=args.registry,
            resurrect_after_days=int(args.resurrect_after_days),
        )

        # Enforce non-truncation policy via capability contract
        run_id = args.run_id or rep.get("run_id") or "unknown"
        ctx = RuneInvocationContext(
            run_id=run_id,
            subsystem_id="abx.a2_registry",
            git_hash="unknown"
        )
        result = invoke_capability(
            capability="evolve.policy.enforce_non_truncation",
            inputs={
                "artifact": rep,
                "raw_full": {
                    "missed": list(rep.get("missed") or []),
                    "resurrected": list(rep.get("resurrected") or []),
                }
            },
            ctx=ctx,
            strict_execution=True
        )
        rep = result["artifact"]

        rep["views"] = {
            "missed_top": list((rep.get("missed") or [])[:40]),
            "resurrected_top": list((rep.get("resurrected") or [])[:40]),
        }
        run_id = args.run_id or rep.get("run_id") or "unknown"
        jpath = os.path.join(args.out_reports, f"a2_missed_{run_id}.json")
        mpath = os.path.join(args.out_reports, f"a2_missed_{run_id}.md")
        _write_json(jpath, rep)
        with open(mpath, "w", encoding="utf-8") as f:
            f.write("# A2 Missed Terms v0.1\n\n")
            f.write(f"- run_id: `{run_id}`\n")
            f.write(f"- present unique terms: `{rep.get('present')}`\n")
            f.write(f"- known registry keys: `{rep.get('known')}`\n")
            f.write(f"- missed: **{len(rep.get('missed') or [])}**\n")
            f.write(f"- resurrected: **{len(rep.get('resurrected') or [])}**\n\n")

            def _emit(title: str, items: list) -> None:
                f.write(f"## {title}\n")
                for term in items[:40]:
                    f.write(
                        f"- **{term.get('term')}** count={term.get('count')} "
                        f"vel/day={float(term.get('velocity_per_day') or 0.0):.2f} "
                        f"novelty={float(term.get('novelty_score') or 0.0):.2f} "
                        f"prop={float(term.get('propagation_score') or 0.0):.2f} "
                        f"risk={float(term.get('manipulation_risk') or 0.0):.2f} "
                        f"tags={term.get('tags')}\n"
                    )
                f.write("\n")

            _emit("Missed (first time ever)", rep.get("missed") or [])
            _emit("Resurrected (returned after absence)", rep.get("resurrected") or [])

        print(f"[A2_REGISTRY] wrote: {jpath}")
        print(f"[A2_REGISTRY] wrote: {mpath}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
