from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

from abraxas.oracle.v2.discover import discover_envelope
from abraxas.oracle.v2.config import load_or_create_config
from abraxas.oracle.v2.bundle import run_bundle


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")


def _parse_evidence(items: list[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for it in items:
        if "=" not in it:
            continue
        k, v = it.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k and v:
            out[k] = v
    return out


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
    p.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="Evidence attachment spec: key=filename (repeatable). Resolved under out/<run_id>/evidence/",
    )
    p.add_argument("--bw-high", type=float, default=20.0, help="BW_HIGH threshold")
    p.add_argument("--mrs-high", type=float, default=70.0, help="MRS_HIGH threshold")
    p.add_argument("--date-iso", default="", help="Override date_iso (optional)")
    p.add_argument("--no-export", action="store_true", help="Disable export")
    p.add_argument("--no-ledger", action="store_true", help="Disable stabilization ledger tick")
    p.add_argument("--validate", action="store_true", help="Enable v2 schema validation (default)")
    p.add_argument("--no-validate", action="store_true", help="Disable v2 schema validation")
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

    do_validate = True if (args.validate or not args.no_validate) else False

    evidence_map = _parse_evidence(args.evidence)
    out = run_bundle(
        envelope=envelope,
        config_hash=cfg_hash,
        out_dir=args.out_dir,
        thresholds=thresholds,
        user_mode_request=user_mode,
        do_stabilization_tick=(not args.no_ledger),
        ledger_path=(args.ledger_path if args.ledger_path else None),
        date_iso=(args.date_iso if args.date_iso else None),
        validate=do_validate,
        attach_evidence_files=(evidence_map if evidence_map else None),
        compute_evidence_hashes=True,
    )
    surface = out["surface"]
    manifest = out["manifest"]

    if not args.no_export:
        # Also emit "latest" pointers for convenience (additive)
        latest_dir = os.path.join(args.out_dir, "latest")
        _write_json(os.path.join(latest_dir, "surface.json"), surface)
        _write_json(os.path.join(latest_dir, "envelope.json"), envelope)
        _write_json(os.path.join(latest_dir, "manifest.json"), manifest)

        print(f"✅ Exported to: {manifest['run_id']}")
        print(f"   Mode: {manifest['governance']['mode']}")
        print(f"   Compliance: {manifest['governance']['compliance_status']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
