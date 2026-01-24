from __future__ import annotations

import argparse
from pathlib import Path

from .engine import load_items_jsonl, run_ase


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="abraxas-ase", description="Abraxas ASE v0.1 - deterministic anagram sweep engine.")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="Run ASE on a JSONL item feed.")
    r.add_argument("--in", dest="inp", required=True, help="Path to JSONL items.")
    r.add_argument("--out", dest="outdir", required=True, help="Output directory.")
    r.add_argument("--date", dest="date", required=True, help="Run date YYYY-MM-DD.")
    r.add_argument("--pfdi-state", dest="pfdi_state", default="", help="Optional prior pfdi_state.json (baseline).")
    r.add_argument("--lanes-dir", dest="lanes_dir", default="", help="Optional lexicon_sources/lanes directory for canary lane.")
    r.add_argument("--tier", dest="tier", default="academic", help="Output tier: psychonaut|academic|enterprise.")
    r.add_argument("--safe-export", dest="safe_export", action="store_true", default=True, help="Strip URLs/text from outputs.")
    r.add_argument("--include-urls", dest="include_urls", action="store_true", help="Include URLs in enterprise outputs.")
    return p


def _infer_pfdi_state(outdir: Path) -> Path | None:
    # if outdir exists and contains pfdi_state.json, use it
    p = outdir / "pfdi_state.json"
    return p if p.exists() else None


def main() -> None:
    p = _build_parser()
    args = p.parse_args()

    if args.cmd == "run":
        inp = Path(args.inp)
        outdir = Path(args.outdir)
        pfdi_state = Path(args.pfdi_state) if args.pfdi_state else None
        lanes_dir = Path(args.lanes_dir) if args.lanes_dir else None
        tier = str(args.tier or "academic").lower()
        safe_export = bool(args.safe_export)
        include_urls = bool(args.include_urls)
        if pfdi_state is None:
            pfdi_state = _infer_pfdi_state(outdir)
        items = load_items_jsonl(inp)
        run_ase(
            items=items,
            date=args.date,
            outdir=outdir,
            pfdi_state_path=pfdi_state,
            lanes_dir=lanes_dir,
            tier=tier,
            safe_export=safe_export,
            include_urls=include_urls,
        )
