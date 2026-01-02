from __future__ import annotations

import argparse
from typing import List, Optional

from abraxas.mda.cli import main as mda_main


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Practice runner for MDA sandbox.")
    p.add_argument("--bundle", default="")
    p.add_argument("--out", default=".sandbox/practice/mda")
    p.add_argument("--run-at", default="1970-01-01T00:00:00Z")
    p.add_argument("--repeat", type=int, default=1)
    p.add_argument("--emit-md", action="store_true")
    p.add_argument("--emit-signal-v2", action="store_true")
    p.add_argument("--signal-schema-check", action="store_true")
    p.add_argument("--emit-jsonl", action="store_true")
    p.add_argument("--ledger", action="store_true")
    p.add_argument("--strict-budgets", action="store_true")
    p.add_argument("--shadow-anagram", action="store_true")
    p.add_argument("--shadow-anagram-watchlist", default="")
    args = p.parse_args(argv)

    argv2 = ["--out", args.out, "--run-at", args.run_at, "--repeat", str(args.repeat)]
    if args.bundle:
        argv2.extend(["--bundle", args.bundle])
    if args.emit_md:
        argv2.append("--emit-md")
    if args.emit_signal_v2:
        argv2.append("--emit-signal-v2")
    if args.signal_schema_check:
        argv2.append("--signal-schema-check")
    if args.shadow_anagram:
        argv2.append("--shadow-anagram")
        if args.shadow_anagram_watchlist.strip():
            argv2.extend(["--shadow-anagram-watchlist", args.shadow_anagram_watchlist])
    return mda_main(argv2)


if __name__ == "__main__":
    raise SystemExit(main())
