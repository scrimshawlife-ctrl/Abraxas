#!/usr/bin/env python3
"""
Offline Event Correlation runner (shadow lane).

Loads stored envelope artifacts from out/**/envelope.json and emits:
  out/event_correlation/drift_report_v1.json

No DB, no websockets, no live ingestion.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Any, Dict, List

from abraxas.analysis.event_correlation import correlate
from abraxas.core.canonical import canonical_json


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(canonical_json(obj) + "\n")


def _infer_artifact_id_from_path(p: str) -> str | None:
    # out/<run_id>/envelope.json -> <run_id>
    base = os.path.basename(os.path.dirname(p))
    return base or None


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run offline event correlation over stored envelopes")
    ap.add_argument("--out-dir", default="out", help="Base output directory (default: out)")
    ap.add_argument(
        "--glob",
        dest="glob_pattern",
        default="**/envelope.json",
        help="Glob under out-dir to find envelope artifacts (default: **/envelope.json)",
    )
    ap.add_argument(
        "--output",
        default="event_correlation/drift_report_v1.json",
        help="Output path relative to out-dir (default: event_correlation/drift_report_v1.json)",
    )
    args = ap.parse_args(argv)

    pattern = os.path.join(args.out_dir, args.glob_pattern)
    paths = sorted(glob.glob(pattern, recursive=True))
    envelopes: List[Dict[str, Any]] = []
    for p in paths:
        env = _read_json(p)
        if isinstance(env, dict) and "artifact_id" not in env:
            aid = _infer_artifact_id_from_path(p)
            if aid:
                env = dict(env)
                env["artifact_id"] = aid
        envelopes.append(env)

    report = correlate(envelopes)
    out_path = os.path.join(args.out_dir, args.output)
    _write_json(out_path, report)
    print(f"Wrote: {out_path}")
    print(f"Artifacts: {report['window']['artifact_count']}")
    print(f"Clusters: {len(report['clusters'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

