from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Tuple

from .fusion_io import fusiongraph_from_json
from .invariance import compute_report, write_report
from .mode_router import render_mode
from .registry import DomainRegistryV1
from .run import run_mda, write_run_artifacts
from .types import FusionGraph, MDARunEnvelope


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _mode_filename(mode: str) -> str:
    if mode == "oracle":
        return "oracle_log.md"
    if mode == "ritual":
        return "ritual_map.md"
    if mode == "analyst":
        return "analyst_console.md"
    return f"{mode}.md"


def main() -> int:
    p = argparse.ArgumentParser(prog="python -m abraxas.mda")
    p.add_argument("--fixture", required=True, help="Path to MDA fixture JSON")
    p.add_argument("--out", default=".sandbox/out/mda_run", help="Output directory")
    p.add_argument("--env", default="sandbox", choices=["sandbox", "dev", "prod"])
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument("--run-at", dest="run_at_iso", default="2026-01-01T00:00:00Z")
    p.add_argument("--mode", default="analyst", choices=["oracle", "ritual", "analyst"])
    p.add_argument("--emit-md", action="store_true", help="Write mode markdown outputs per run")
    p.add_argument("--repeat", type=int, default=12)
    p.add_argument("--version", default="0.0.0", help="Abraxas version string")
    p.add_argument("--domains", default="*", help="Comma list of domains or '*'")
    p.add_argument(
        "--subdomains", default="*", help="Comma list of domain:subdomain pairs or '*'"
    )
    args = p.parse_args()

    fixture = _load_json(args.fixture)
    vectors = fixture.get("vectors", {}) or {}
    registry = DomainRegistryV1.from_vectors(vectors)

    envelope = MDARunEnvelope(
        env=str(args.env),
        run_at_iso=str(args.run_at_iso),
        seed=int(args.seed),
        fixture_path=str(args.fixture),
    )

    dsp_runs: List[Tuple[Any, ...]] = []
    fusion_runs: List[FusionGraph] = []

    for i in range(int(args.repeat)):
        run_dir = os.path.join(args.out, f"run_{i+1:02d}")
        dsps, out = run_mda(
            envelope,
            abraxas_version=args.version,
            registry=registry,
            domains=args.domains,
            subdomains=args.subdomains,
        )
        write_run_artifacts(out, run_dir)
        dsp_runs.append(dsps)
        fusion_runs.append(fusiongraph_from_json(out["fusion_graph"]))

        if args.emit_md:
            rendered = render_mode(out, mode=args.mode)
            with open(os.path.join(run_dir, _mode_filename(args.mode)), "w", encoding="utf-8") as f:
                f.write(rendered.markdown)

    report = compute_report(envelope, dsp_runs=dsp_runs, fusion_runs=fusion_runs)
    write_report(report, os.path.join(args.out, "invariance_report.json"))
    return 0

