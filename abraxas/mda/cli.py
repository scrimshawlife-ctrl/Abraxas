from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return obj


def _write_json(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def _canonical_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return s.encode("utf-8")


def _sha256_hex(obj: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(obj)).hexdigest()


def _run_dir(out_dir: str, run_index: int) -> str:
    return os.path.join(out_dir, f"run_{run_index:02d}")


def _signal_v2_payload(
    *,
    canon_hash: str,
    run_index: int,
    repeat: int,
    mode: str,
    version: str,
    env: str,
    seed: int,
    run_at: str,
) -> Dict[str, Any]:
    return {
        "oracle_signal_v2": {
            "mda_v1_1": {
                "canon_hash": canon_hash,
                "run_index": run_index,
            },
            "meta": {
                "slice_hash": canon_hash,
                "repeat": repeat,
                "mode": mode,
                "version": version,
                "env": env,
                "seed": seed,
                "run_at": run_at,
            },
        }
    }


def _validate_signal_v2(sig: Dict[str, Any]) -> None:
    osv2 = sig.get("oracle_signal_v2")
    if not isinstance(osv2, dict):
        raise ValueError("signal_v2.json missing 'oracle_signal_v2' object")
    if "mda_v1_1" not in osv2 or not isinstance(osv2["mda_v1_1"], dict):
        raise ValueError("signal_v2.json missing 'oracle_signal_v2.mda_v1_1' object")
    meta = osv2.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("signal_v2.json missing 'oracle_signal_v2.meta' object")
    if not meta.get("slice_hash"):
        raise ValueError("signal_v2.json missing 'oracle_signal_v2.meta.slice_hash'")


def _write_jsonl(path: str, lines: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for obj in lines:
            f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True))
            f.write("\n")


@dataclass(frozen=True)
class RunResult:
    run_index: int
    canon_hash: str
    signal_hash: Optional[str]


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="abraxas.mda")
    p.add_argument("--fixture", required=True)
    p.add_argument("--bundle", required=True)
    p.add_argument("--toggle-file", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--repeat", type=int, default=12)
    p.add_argument("--mode", default="analyst", choices=["oracle", "ritual", "analyst"])
    p.add_argument("--version", default="2.2.0")
    p.add_argument("--env", default="sandbox", choices=["sandbox", "dev", "prod"])
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument("--run-at", default="2026-01-01T00:00:00Z")
    p.add_argument("--emit-md", action="store_true")
    p.add_argument("--emit-signal-v2", action="store_true")
    p.add_argument("--signal-schema-check", action="store_true")
    p.add_argument("--emit-jsonl", default=None)
    p.add_argument("--ledger", default=None)
    p.add_argument("--strict-budgets", action="store_true")
    args = p.parse_args(argv)

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    fixture = _read_json(args.fixture)
    bundle = _read_json(args.bundle)
    toggles = _read_json(args.toggle_file)

    # CANON: all fields that must remain invariant across repeated runs.
    canon = {
        "fixture": fixture,
        "bundle": bundle,
        "toggles": toggles,
        "mode": args.mode,
        "version": args.version,
        "env": args.env,
        "seed": args.seed,
        "run_at": args.run_at,
        "strict_budgets": bool(args.strict_budgets),
    }
    canon_hash = _sha256_hex(canon)

    run_results: List[RunResult] = []
    jsonl_events: List[Dict[str, Any]] = []
    for i in range(1, int(args.repeat) + 1):
        rd = _run_dir(out_dir, i)
        os.makedirs(rd, exist_ok=True)

        # Optional: emit a tiny markdown summary for humans (RENDER).
        if args.emit_md:
            md_path = os.path.join(rd, "summary.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("# MDA Practice Run\n\n")
                f.write(f"- run_index: {i}\n")
                f.write(f"- canon_hash: {canon_hash}\n")
                f.write(f"- env: {args.env}\n")
                f.write(f"- mode: {args.mode}\n")
                f.write(f"- run_at: {args.run_at}\n")

        signal_hash: Optional[str] = None
        if args.emit_signal_v2:
            sig = _signal_v2_payload(
                canon_hash=canon_hash,
                run_index=i,
                repeat=int(args.repeat),
                mode=args.mode,
                version=args.version,
                env=args.env,
                seed=int(args.seed),
                run_at=args.run_at,
            )
            if args.signal_schema_check:
                _validate_signal_v2(sig)
            sig_path = os.path.join(rd, "signal_v2.json")
            _write_json(sig_path, sig)
            signal_hash = _sha256_hex(sig)

        run_results.append(RunResult(run_index=i, canon_hash=canon_hash, signal_hash=signal_hash))
        jsonl_events.append(
            {
                "type": "mda_practice_event",
                "run_index": i,
                "canon_hash": canon_hash,
                "signal_hash": signal_hash,
            }
        )

    # Invariance report: governance property check for repeated runs.
    unique_canon = sorted({r.canon_hash for r in run_results})
    canon_invariant = len(unique_canon) == 1
    drift_class = "none" if canon_invariant else "canon"
    inv = {
        "repeat": int(args.repeat),
        "canon_invariant": canon_invariant,
        "drift_class": drift_class,
        "canon_hashes": unique_canon,
        "canon_hash": canon_hash,
    }
    _write_json(os.path.join(out_dir, "invariance_report.json"), inv)

    if args.emit_jsonl:
        _write_jsonl(args.emit_jsonl, jsonl_events)

    if args.ledger:
        ledger = {
            "meta": {
                "repeat": int(args.repeat),
                "mode": args.mode,
                "version": args.version,
                "env": args.env,
                "seed": int(args.seed),
                "run_at": args.run_at,
            },
            "canon_hash": canon_hash,
            "runs": [
                {
                    "run_index": r.run_index,
                    "canon_hash": r.canon_hash,
                    "signal_hash": r.signal_hash,
                }
                for r in run_results
            ],
        }
        _write_json(args.ledger, ledger)

    return 0

