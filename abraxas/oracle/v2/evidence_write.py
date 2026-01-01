from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, Optional

from abraxas.oracle.v2.discover import discover_envelope
from abraxas.oracle.v2.export import compute_run_id
from abraxas.oracle.v2.evidence_convention import evidence_dir_for_envelope, attach_evidence_from_run_dir
from abraxas.oracle.v2.render import render_by_mode


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")


def _load_payload(args) -> Any:
    if args.json:
        return json.loads(args.json)
    if args.json_file:
        return _read_json(args.json_file)
    raise SystemExit("Must provide --json or --json-file")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="abraxas.oracle.v2.evidence_write")
    p.add_argument("--out-dir", default="out", help="Base output dir (default: out)")
    p.add_argument("--in-envelope", default="", help="Path to envelope.json (optional; else auto-discover)")
    p.add_argument("--v1-out-dir", default="out", help="Search base for auto-discovery (default: out)")
    p.add_argument("--name", required=True, help="Evidence name key (e.g., news, slang_corpus)")
    p.add_argument("--filename", default="", help="Override filename (default: <name>.json)")
    p.add_argument("--json", default="", help="JSON payload string")
    p.add_argument("--json-file", default="", help="Path to a JSON file to write")
    p.add_argument("--no-hash", action="store_true", help="Do not compute evidence file hashes")
    p.add_argument("--refresh-latest-surface", action="store_true", help="Re-render and rewrite out/latest/surface.json")
    args = p.parse_args(argv)

    # Load envelope
    if args.in_envelope:
        envelope = _read_json(args.in_envelope)
    else:
        _, env = discover_envelope(v1_out_dir=args.v1_out_dir)
        if env is None:
            raise SystemExit("Could not auto-discover an envelope.json to attach evidence to")
        envelope = env

    payload = _load_payload(args)

    # Compute deterministic run location
    run_id = compute_run_id(envelope)
    ev_dir = evidence_dir_for_envelope(envelope, out_dir=args.out_dir)
    os.makedirs(ev_dir, exist_ok=True)

    name = args.name.strip()
    if not name:
        raise SystemExit("--name must be non-empty")
    fname = args.filename.strip() if args.filename else f"{name}.json"
    ev_path = os.path.join(ev_dir, fname)

    # Write evidence payload
    _write_json(ev_path, payload)

    # Attach pointers (only existing) and rewrite envelope artifacts
    attach_evidence_from_run_dir(
        envelope=envelope,
        out_dir=args.out_dir,
        files={name: fname},
        compute_hashes=(not args.no_hash),
    )

    # Update run envelope + latest envelope
    run_env_path = os.path.join(args.out_dir, run_id, "envelope.json")
    latest_env_path = os.path.join(args.out_dir, "latest", "envelope.json")
    _write_json(run_env_path, envelope)
    _write_json(latest_env_path, envelope)

    if args.refresh_latest_surface:
        surface = render_by_mode(envelope)
        _write_json(os.path.join(args.out_dir, "latest", "surface.json"), surface)

    print(ev_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
