from __future__ import annotations

import argparse
import json
import os
from typing import List, Optional

from .run import run_mda
from .signal_layer_v2 import mda_to_oracle_signal_v2, shallow_schema_check


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Run MDA sandbox pipeline.")
    p.add_argument("--bundle", default="", help="JSON bundle to process")
    p.add_argument("--out", default=".sandbox/practice/mda", help="Output directory")
    p.add_argument("--run-at", default="1970-01-01T00:00:00Z")
    p.add_argument("--repeat", type=int, default=1)
    p.add_argument("--version", default="dev")
    p.add_argument("--emit-md", action="store_true")
    p.add_argument("--emit-signal-v2", action="store_true")
    p.add_argument("--signal-schema-check", action="store_true")
    p.add_argument("--shadow-anagram", action="store_true")
    p.add_argument("--shadow-anagram-watchlist", default="", help="Comma list of watch tokens (raw strings)")
    args = p.parse_args(argv)

    payload = None
    if args.bundle:
        with open(args.bundle, "r", encoding="utf-8") as f:
            payload = json.load(f)

    watchlist = tuple()
    if args.shadow_anagram_watchlist:
        watchlist = tuple(x.strip() for x in args.shadow_anagram_watchlist.split(",") if x.strip())

    os.makedirs(args.out, exist_ok=True)

    for i in range(1, args.repeat + 1):
        env = {
            "run_at": args.run_at,
            "run_idx": i,
        }
        _, out = run_mda(env, abraxas_version=args.version, registry=None)

        if args.shadow_anagram:
            from .shadow_hooks import apply_shadow_anagram_detectors
            ctx = {"domain": "unknown", "subdomain": "unknown"}
            out = apply_shadow_anagram_detectors(
                mda_out=out,
                payload=payload,
                context=ctx,
                run_at_iso=args.run_at,
                out_dir=args.out,
                watchlist_tokens=watchlist,
            )

        run_dir = os.path.join(args.out, f"run_{i:02d}")
        os.makedirs(run_dir, exist_ok=True)

        if args.emit_md:
            with open(os.path.join(run_dir, "mda.md"), "w", encoding="utf-8") as f:
                f.write("# MDA Sandbox Output\n")

        if args.emit_signal_v2:
            sig = mda_to_oracle_signal_v2(out)
            if args.signal_schema_check:
                shallow_schema_check(sig)
            with open(os.path.join(run_dir, "signal_v2.json"), "w", encoding="utf-8") as f:
                json.dump(sig, f, ensure_ascii=False, indent=2, sort_keys=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
