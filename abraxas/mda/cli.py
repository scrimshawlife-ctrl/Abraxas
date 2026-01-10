from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, Optional

from .signal_layer_v2 import mda_to_oracle_signal_v2, shallow_schema_check


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _write_json(path: str, obj: Any) -> None:
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def _append_jsonl(path: str, obj: Any) -> None:
    _ensure_parent_dir(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True))
        f.write("\n")


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="python -m abraxas.mda")
    p.add_argument("--out", default=".sandbox/mda", help="Output directory for run artifacts")
    p.add_argument("--repeat", type=int, default=1, help="Number of deterministic runs to emit")
    p.add_argument("--fixture", required=True, help="Path to MDA output fixture JSON (practice-run output)")
    p.add_argument("--bundle", default=None, help="Evidence bundle JSON path (optional; accepted for compatibility)")
    p.add_argument("--toggle-file", default=None, help="Toggles JSON path (optional; accepted for compatibility)")
    p.add_argument("--strict-budgets", action="store_true", help="Accepted for compatibility; no-op in this drop")
    p.add_argument("--emit-md", action="store_true", help="Emit a lightweight markdown projection")
    p.add_argument("--mode", default="analyst", help="Markdown mode name (used only for filename)")
    p.add_argument("--emit-jsonl", default=None, help="Append replay stream JSONL at path (optional)")
    p.add_argument("--ledger", default=None, help="Write session ledger JSON at path (optional)")
    p.add_argument("--emit-signal-v2", action="store_true", help="Write Oracle Signal Layer v2 slice (signal_v2.json)")
    p.add_argument("--signal-schema-check", action="store_true", help="Shallow check of signal v2 output shape")
    p.add_argument("--version", default="0.0.0", help="Abraxas version string")
    args = p.parse_args(argv)

    fixture = _load_json(args.fixture)

    # Compatibility: accept bundle/toggles even if unused in this drop.
    if args.bundle:
        _ = _load_json(args.bundle)
    if args.toggle_file:
        _ = _load_json(args.toggle_file)

    run_summaries = []
    slice_hashes = []

    for i in range(max(args.repeat, 1)):
        run_id = f"run_{i+1:02d}"
        run_dir = os.path.join(args.out, run_id)
        os.makedirs(run_dir, exist_ok=True)

        # Always emit the base fixture as the "MDA output" artifact for traceability.
        _write_json(os.path.join(run_dir, "mda_out.json"), fixture)

        artifacts = ["mda_out.json"]

        if args.emit_md:
            md_path = os.path.join(run_dir, f"{args.mode}.md")
            md = "\n".join(
                [
                    f"# MDA ({args.mode})",
                    "",
                    f"- fixture: `{os.path.basename(args.fixture)}`",
                    f"- version: `{args.version}`",
                    "",
                ]
            )
            _ensure_parent_dir(md_path)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md)
            artifacts.append(f"{args.mode}.md")

        if args.emit_signal_v2:
            sig = mda_to_oracle_signal_v2(fixture)
            if args.signal_schema_check:
                shallow_schema_check(sig)
            _write_json(os.path.join(run_dir, "signal_v2.json"), sig)
            artifacts.append("signal_v2.json")
            slice_hashes.append(sig["oracle_signal_v2"]["meta"]["slice_hash"])

        summary = {
            "run_id": run_id,
            "run_dir": run_dir,
            "artifacts": artifacts,
            "envelope": fixture.get("envelope", {}),
        }
        run_summaries.append(summary)

        if args.emit_jsonl:
            _append_jsonl(
                args.emit_jsonl,
                {
                    "run_id": run_id,
                    "envelope": fixture.get("envelope", {}),
                    "signal_v2": bool(args.emit_signal_v2),
                },
            )

    # Simple invariance report: counts + unique slice hashes (when enabled).
    invariance_report = {
        "repeat": max(args.repeat, 1),
        "signal_v2_enabled": bool(args.emit_signal_v2),
        "slice_hash_unique_count": len(sorted(set(slice_hashes))) if slice_hashes else 0,
        "slice_hashes": sorted(set(slice_hashes)) if slice_hashes else [],
    }
    _write_json(os.path.join(args.out, "invariance_report.json"), invariance_report)

    if args.ledger:
        session = {
            "tool": "abraxas.mda",
            "version": args.version,
            "out": args.out,
            "runs": run_summaries,
            "invariance_report": os.path.join(args.out, "invariance_report.json"),
        }
        _write_json(args.ledger, session)

    return 0

