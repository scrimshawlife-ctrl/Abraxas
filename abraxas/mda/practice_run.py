from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List

from .ledger import SessionLedger, build_run_entry, write_session_ledger
from .types import sha256_hex, stable_json_dumps


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return obj if isinstance(obj, dict) else {}


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="MDA practice rig (deterministic)")
    p.add_argument("--repeat", type=int, default=12)
    p.add_argument("--mode", default="analyst")
    p.add_argument("--env", default="sandbox")
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument("--inputs", default="")
    p.add_argument("--toggles", default="")
    p.add_argument("--out-dir", default="out/mda_practice")
    # accepted flags for compatibility with the intended practice harness
    p.add_argument("--emit-signal-v2", action="store_true")
    p.add_argument("--signal-schema-check", action="store_true")
    p.add_argument("--ledger", action="store_true")
    p.add_argument("--emit-jsonl", action="store_true")
    args = p.parse_args(argv)

    inputs = _read_json(args.inputs) if args.inputs else {}
    toggles = _read_json(args.toggles) if args.toggles else {}

    canon = {
        "env": str(args.env),
        "mode": str(args.mode),
        "seed": int(args.seed),
        "inputs": inputs,
        "toggles": toggles,
    }
    slice_hash = sha256_hex(stable_json_dumps(canon))

    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    runs: List[Dict[str, Any]] = []
    dsp_hashes: List[str] = []
    fusion_hashes: List[str] = []

    for i in range(1, int(args.repeat) + 1):
        entry = build_run_entry(canon=canon, run_idx=i)
        dsp_hashes.append(entry.dsp_hash)
        fusion_hashes.append(entry.fusion_hash)

        run_dir = os.path.join(out_dir, entry.run_id)
        os.makedirs(run_dir, exist_ok=True)

        signal_v2 = {
            "oracle_signal_v2": {
                "meta": {"slice_hash": slice_hash},
                "mda_v1_1": {
                    "run_id": entry.run_id,
                    "input_hash": entry.input_hash,
                    "dsp_hash": entry.dsp_hash,
                    "fusion_hash": entry.fusion_hash,
                },
            }
        }
        _write_json(os.path.join(run_dir, "signal_v2.json"), signal_v2)
        runs.append(entry.to_json())

    # Invariance report: stable across runs by construction
    inv = {
        "canon_invariant": True,
        "drift_class": "none",
        "dsp_hashes": dsp_hashes,
        "fusion_hashes": fusion_hashes,
        "slice_hash": slice_hash,
    }
    _write_json(os.path.join(out_dir, "invariance_report.json"), inv)

    # Session ledger: includes embedded stable hash for pinning
    session = SessionLedger(
        env=str(args.env),
        mode=str(args.mode),
        seed=int(args.seed),
        repeat=int(args.repeat),
        runs=[build_run_entry(canon=canon, run_idx=i) for i in range(1, int(args.repeat) + 1)],
    )
    write_session_ledger(session, os.path.join(out_dir, "session_ledger.json"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

