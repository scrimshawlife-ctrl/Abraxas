from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

from abraxas.mda.cli import main as mda_cli_main


def _write_tmp_json(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def build_default_fixture_path() -> str:
    # Keep deterministic and repo-local
    return os.path.join("abraxas", "mda", "fixtures", "daily_oracle_v1.json")


def build_default_bundle_path() -> str:
    return os.path.join("abraxas", "mda", "fixtures", "evidence_bundle_sample.json")


def build_default_toggle_path() -> str:
    return os.path.join("abraxas", "mda", "fixtures", "toggles_minimal.json")


def main() -> int:
    p = argparse.ArgumentParser(prog="abraxas.sandbox.mda_practice")
    p.add_argument("--out", default=os.path.join(".sandbox", "practice", "mda"))
    p.add_argument("--repeat", type=int, default=12)
    p.add_argument("--mode", default="analyst", choices=["oracle", "ritual", "analyst"])
    p.add_argument("--version", default="2.2.0")
    p.add_argument("--env", default="sandbox", choices=["sandbox", "dev", "prod"])
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument("--run-at", default="2026-01-01T00:00:00Z")
    p.add_argument("--fixture", default=build_default_fixture_path())
    p.add_argument("--bundle", default=build_default_bundle_path())
    p.add_argument("--toggles", default=build_default_toggle_path())
    p.add_argument("--emit-md", action="store_true")
    p.add_argument("--emit-signal-v2", action="store_true")
    p.add_argument("--signal-schema-check", action="store_true")
    p.add_argument("--emit-jsonl", action="store_true")
    p.add_argument("--ledger", action="store_true")
    p.add_argument("--strict-budgets", action="store_true")
    args = p.parse_args()

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    jsonl_path = os.path.join(out_dir, "replay.jsonl") if args.emit_jsonl else None
    ledger_path = os.path.join(out_dir, "session_ledger.json") if args.ledger else None

    # Reuse existing MDA CLI deterministically by constructing argv.
    argv = [
        "abraxas.mda",
        "--fixture",
        args.fixture,
        "--bundle",
        args.bundle,
        "--toggle-file",
        args.toggles,
        "--out",
        out_dir,
        "--repeat",
        str(args.repeat),
        "--mode",
        args.mode,
        "--version",
        args.version,
        "--env",
        args.env,
        "--seed",
        str(args.seed),
        "--run-at",
        args.run_at,
    ]

    if args.strict_budgets:
        argv.append("--strict-budgets")
    if args.emit_md:
        argv.extend(["--emit-md"])
    if args.emit_signal_v2:
        argv.extend(["--emit-signal-v2"])
    if args.signal_schema_check:
        argv.extend(["--signal-schema-check"])
    if jsonl_path:
        argv.extend(["--emit-jsonl", jsonl_path])
    if ledger_path:
        argv.extend(["--ledger", ledger_path])

    # Monkeypatch sys.argv for CLI reuse (keeps behavior in one place)
    import sys

    old = sys.argv[:]
    try:
        sys.argv = argv
        return mda_cli_main()
    finally:
        sys.argv = old


if __name__ == "__main__":
    raise SystemExit(main())

