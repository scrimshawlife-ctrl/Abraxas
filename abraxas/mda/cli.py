from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Tuple

from .adapters.router import AdapterRouter
from .budget import BudgetCaps, enforce_caps
from .fusion_io import fusiongraph_from_json
from .invariance import compute_report, write_report
from .ledger import SessionLedger, build_run_entry, write_run_manifest, write_session_ledger
from .mode_router import render_mode
from .registry import DomainRegistryV1
from .replay import append_jsonl
from .run import run_mda, write_run_artifacts
from .toggles import load_toggle_file
from .types import MDARunEnvelope, FusionGraph


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    p = argparse.ArgumentParser(prog="abraxas.mda", description="MDA deterministic practice runner")
    p.add_argument("--fixture", required=True, help="MDA fixture JSON (inputs envelope)")
    p.add_argument("--out", default=".sandbox/out/mda_run", help="Output directory")
    p.add_argument("--env", default="dev", help="Environment tag")
    p.add_argument("--run-at", default="1970-01-01T00:00:00Z", help="Run timestamp (ISO, caller-provided)")
    p.add_argument("--seed", type=int, default=1, help="Deterministic seed")
    p.add_argument("--repeat", type=int, default=1, help="Repeat runs (same envelope) for invariance checks")

    p.add_argument("--emit-md", action="store_true", help="Emit markdown projection per run")
    p.add_argument("--mode", default="analyst", help="Render mode for markdown projection")

    p.add_argument("--bundle", default=None, help="Evidence bundle JSON to adapt into vectors (optional)")
    p.add_argument("--toggle-file", default=None, help="Toggle matrix JSON to constrain subdomains (optional)")
    p.add_argument("--strict-budgets", action="store_true", help="Enforce deterministic sandbox caps")
    p.add_argument("--emit-jsonl", default=None, help="Append replay stream JSONL at path (optional)")
    p.add_argument("--ledger", default=None, help="Write session ledger JSON at path (optional)")

    p.add_argument("--version", default="0.0.0", help="Abraxas version string")
    p.add_argument("--domains", default="*", help="Comma list of domains or '*'")
    p.add_argument("--subdomains", default="*", help="Comma list of domain:subdomain or '*'")

    args = p.parse_args()

    fixture = _load_json(args.fixture)
    inputs = fixture.get("inputs") or {}

    # If bundle provided, adapt it into inputs["vectors"]
    if args.bundle:
        bundle = _load_json(args.bundle)
        _reg = DomainRegistryV1()
        router = AdapterRouter()
        adapted = router.adapt(bundle, registry=_reg)
        inputs = dict(inputs)
        inputs["vectors"] = adapted.vectors
        inputs["adapter_notes"] = adapted.notes

    registry = DomainRegistryV1()

    enabled_domains = tuple(registry.domains()) if args.domains.strip() == "*" else tuple(
        x.strip() for x in args.domains.split(",") if x.strip()
    )
    enabled_subdomains = tuple(registry.all_subdomain_keys()) if args.subdomains.strip() == "*" else tuple(
        x.strip() for x in args.subdomains.split(",") if x.strip()
    )

    # Toggle file can further constrain enabled_subdomains
    if args.toggle_file:
        toggles = _load_json(args.toggle_file)
        toggled = load_toggle_file(toggles)
        if toggled:
            enabled_subdomains = tuple(x for x in enabled_subdomains if x in set(toggled))

    if args.strict_budgets:
        caps = BudgetCaps()
        enforce_caps(caps=caps, domain_count=len(enabled_domains), subdomain_count=len(enabled_subdomains))

    envelope = MDARunEnvelope(
        env=args.env,
        run_at_iso=args.run_at,
        seed=args.seed,
        promotion_enabled=False,
        enabled_domains=enabled_domains,
        enabled_subdomains=enabled_subdomains,
        inputs=inputs,
    )

    os.makedirs(args.out, exist_ok=True)

    dsp_runs: List[Tuple[Any, ...]] = []
    fusion_runs: List[FusionGraph] = []
    ledger_entries = []
    session_id = os.path.basename(os.path.normpath(args.out)) or "mda_session"

    for i in range(args.repeat):
        run_dir = os.path.join(args.out, f"run_{i+1:02d}")
        dsps, out = run_mda(envelope, abraxas_version=args.version, registry=registry)
        write_run_artifacts(out, run_dir)
        dsp_runs.append(tuple(dsps))
        fusion_runs.append(fusiongraph_from_json(out["fusion_graph"]))

        # Emit markdown projection
        artifacts: List[str] = []
        if args.emit_md:
            rendered = render_mode(out, mode=args.mode)
            with open(os.path.join(run_dir, f"{args.mode}.md"), "w", encoding="utf-8") as f:
                f.write(rendered.markdown)
            artifacts.append(f"{args.mode}.md")

        # Run manifest + optional replay stream
        entry = build_run_entry(
            run_id=f"run_{i+1:02d}",
            run_dir=run_dir,
            envelope_json=out.get("envelope", {}),
            out=out,
            mode=args.mode,
            artifacts=artifacts,
            notes=str((inputs or {}).get("adapter_notes", "")),
        )
        write_run_manifest(entry, os.path.join(run_dir, "run_manifest.json"))
        ledger_entries.append(entry)

        if args.emit_jsonl:
            append_jsonl(
                args.emit_jsonl,
                {
                    "run_id": entry.run_id,
                    "input_hash": entry.input_hash,
                    "dsp_hash": entry.dsp_hash,
                    "fusion_hash": entry.fusion_hash,
                    "mode": entry.mode,
                    "envelope": out.get("envelope", {}),
                },
            )

    report = compute_report(envelope, dsp_runs=dsp_runs, fusion_runs=fusion_runs)
    write_report(report, os.path.join(args.out, "invariance_report.json"))

    if args.ledger:
        session = SessionLedger(
            session_id=session_id,
            version=args.version,
            env=args.env,
            seed=args.seed,
            run_at=args.run_at,
            entries=tuple(ledger_entries),
        )
        write_session_ledger(session, args.ledger)

    return 0

