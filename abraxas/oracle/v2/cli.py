from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

from abraxas.oracle.v2.discover import discover_envelope
from abraxas.oracle.v2.config import load_or_create_config
from abraxas.oracle.v2.orchestrate import attach_v2
from abraxas.oracle.v2.render import render_by_mode
from abraxas.oracle.v2.export import export_run


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    """
    V2 Oracle CLI: runs compliance → routing → ledger → render → export.
    """
    p = argparse.ArgumentParser(description="Oracle v2 governance runner")
    p.add_argument("--config-hash", default="", help="Deterministic config hash for provenance (optional if --config used)")
    p.add_argument("--config", default="", help="Path to v2 config json (auto-created if missing when provided)")
    p.add_argument("--profile", default="default", help="Config profile (default: default)")
    p.add_argument("--schema-index", default="", help="Schema index path (default: schema/v2/index.json)")
    p.add_argument("--in-envelope", default="", help="Path to an existing envelope.json (optional)")
    p.add_argument("--auto-in-envelope", action="store_true",
                   help="Auto-discover an existing v1 envelope.json (out/latest/envelope.json etc.)")
    p.add_argument("--v1-out-dir", default="out", help="Base dir to search for v1 envelopes (default: out)")
    p.add_argument("--out-dir", default="out", help="Base output directory (default: out)")
    p.add_argument("--ledger-path", default="", help="Override stabilization ledger path (optional)")
    p.add_argument("--mode", default="", choices=["", "SNAPSHOT", "ANALYST", "RITUAL"], help="User mode request (optional)")
    p.add_argument("--bw-high", type=float, default=20.0, help="BW_HIGH threshold")
    p.add_argument("--mrs-high", type=float, default=70.0, help="MRS_HIGH threshold")
    p.add_argument("--date-iso", default="", help="Override date_iso (optional)")
    p.add_argument("--no-export", action="store_true", help="Disable export")
    p.add_argument("--no-ledger", action="store_true", help="Disable stabilization ledger tick")
    args = p.parse_args(argv)

    # Resolve config_hash
    cfg_hash = args.config_hash
    if not cfg_hash:
        if args.config:
            cfg, h = load_or_create_config(
                path=args.config,
                profile=args.profile,
                bw_high=float(args.bw_high),
                mrs_high=float(args.mrs_high),
                ledger_enabled=(not args.no_ledger),
                schema_index_path=(args.schema_index if args.schema_index else None) or "schema/v2/index.json",
            )
            cfg_hash = h
        else:
            raise SystemExit("--config-hash is required unless --config is provided")

    envelope: Dict[str, Any]
    if args.in_envelope:
        envelope = _read_json(args.in_envelope)
    elif args.auto_in_envelope:
        path, env = discover_envelope(v1_out_dir=args.v1_out_dir)
        if env is not None:
            envelope = env
            print(f"📂 Auto-discovered envelope: {path}")
        else:
            print("⚠️  No v1 envelope found, using minimal shell")
            envelope = {"oracle_signal": {"scores_v1": {}, "window": None}}
    else:
        envelope = {"oracle_signal": {"scores_v1": {}, "window": None}}

    thresholds = {"BW_HIGH": float(args.bw_high), "MRS_HIGH": float(args.mrs_high)}
    user_mode = args.mode if args.mode else None

    attach_v2(
        envelope=envelope,
        config_hash=cfg_hash,
        thresholds=thresholds,
        user_mode_request=user_mode,
        do_stabilization_tick=not args.no_ledger,
        ledger_path=args.ledger_path if args.ledger_path else None,
        date_iso=args.date_iso if args.date_iso else None,
    )

    surface = render_by_mode(envelope)

    if not args.no_export:
        manifest = export_run(envelope=envelope, surface=surface, out_dir=args.out_dir)
        print(f"✅ Exported to: {manifest['run_id']}")
        print(f"   Mode: {manifest['governance']['mode']}")
        print(f"   Compliance: {manifest['governance']['compliance_status']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
