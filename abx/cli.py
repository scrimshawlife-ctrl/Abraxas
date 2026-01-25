"""ABX CLI - Abraxas Boot eXtensions command-line interface.

Subcommands:
- doctor: Check system readiness for Orin deployment
- up: Start HTTP server with health endpoints
- smoke: Run deterministic smoke test
- assets sync: Generate asset manifest
- overlay: Manage overlay lifecycle (list/status/install/start/stop)
- drift: Detect configuration and code drift (snapshot/check)
- watchdog: Health monitoring with auto-restart
- update: Atomic update with rollback
- ingest: Run always-on Decodo ingestion scheduler
- ui: Start chat-like UI server
- admin: Print admin handshake (module discovery)
- aalmanac-admin: AALmanac review system admin CLI
- lens: Local Evaluation & Notation Studio (admin training mode)
- diag deps: Check optional dependency availability for LENS
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import typer

from abx.kernel import invoke
from abx.runtime.config import load_config
from abx.assets.manifest import write_manifest, read_manifest
from abx.runtime.provenance import make_provenance, compute_config_hash
from abx.core.pipeline import run_oracle
from abx.util.jsonutil import dumps_stable, dump_file
from abx.overlays.manager import OverlayManager
from abx.runtime.drift import take_snapshot, save_snapshot, check_drift
from abx.runtime.watchdog import watchdog_loop
from abraxas.cli.aalmanac_cmd import app as aalmanac_app
from abraxas.cli.aalmanac_review_cmd import app as aalmanac_review_app
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability
from abx.runtime.updater import update_atomic
from abx.ingest.scheduler import run_ingest_forever
from abx.ui.server import build_ui_app
from abx.ui.admin_handshake import admin_prompt
from abx.plugins import load_plugins
from abraxas.admin.kite.cli import register as register_kite

typer_app = typer.Typer(help="ABX admin toolset.")
typer_app.add_typer(aalmanac_app, name="aalmanac")
typer_app.add_typer(aalmanac_review_app, name="aalmanac-admin")

def _cmd_ok(msg: str) -> None:
    """Print success message."""
    print(msg)

def _cmd_err(msg: str) -> None:
    """Print error message to stderr."""
    print(msg, file=sys.stderr)

def doctor(args: argparse.Namespace) -> int:
    """Run system diagnostics and readiness checks via kernel.invoke."""
    response = invoke(
        rune_id="abx.doctor",
        payload={
            "diagnostic_level": args.level,
            "seed": args.seed,
            "full": args.full,
            "emit": args.emit,
        },
        context={},
    )
    result = response["result"]
    print(dumps_stable(result))
    return 0 if result.get("ok") else 2

def compress_cmd(args: argparse.Namespace) -> int:
    """Run compression detection via kernel.invoke."""
    lexicon = []
    if args.lexicon_file:
        with open(args.lexicon_file, "r", encoding="utf-8") as file:
            lexicon = json.load(file)

    response = invoke(
        rune_id="compression.detect",
        payload={
            "text_event": args.text,
            "lexicon": lexicon,
            "seed": args.seed,
            "config": {"domain": args.domain},
        },
        context={},
    )
    print(dumps_stable(response))
    return 0


def self_heal_cmd(args: argparse.Namespace) -> int:
    from abx.self_heal_cli import run as run_self_heal

    return run_self_heal(args)


def govern_cmd(args: argparse.Namespace) -> int:
    from abx.govern_cli import run as run_govern

    return run_govern(args)


def apply_cmd(args: argparse.Namespace) -> int:
    from abx.apply_cli import run as run_apply

    return run_apply(args)

def _lens_missing_deps() -> list[str]:
    import importlib

    deps = ["fastapi", "uvicorn", "jinja2", "multipart"]
    return [name for name in deps if importlib.util.find_spec(name) is None]

def diag_deps_cmd() -> int:
    """Check optional dependency availability for LENS."""
    print("deps: OK (core)")
    missing = _lens_missing_deps()
    if missing:
        missing_list = ", ".join(missing)
        print(f"deps: MISSING (lens) missing={missing_list} -> install: pip install -e \".[lens]\"")
        return 1
    print("deps: OK (lens)")
    return 0

def diag_cmd(args: argparse.Namespace) -> int:
    if args.diag_action == "deps":
        return diag_deps_cmd()
    raise RuntimeError("unknown diag action")

def _register_lens_typer() -> None:
    from abraxas.cli.lens_cmd import app as lens_app

    typer_app.add_typer(lens_app, name="lens")

_register_lens_typer()
def assets_sync() -> int:
    """Generate and write asset manifest."""
    cfg = load_config()
    p = write_manifest(cfg.assets_dir)
    _cmd_ok(f"Wrote {p}")
    m = read_manifest(cfg.assets_dir)
    print(dumps_stable(m))
    return 0

def smoke() -> int:
    """Run deterministic smoke test with provenance."""
    cfg = load_config()
    cfg_hash = compute_config_hash({
        "profile": cfg.profile,
        "assets_dir": str(cfg.assets_dir),
        "overlays_dir": str(cfg.overlays_dir),
        "state_dir": str(cfg.state_dir),
        "http": [cfg.http_host, cfg.http_port],
        "concurrency": cfg.concurrency,
    })
    manifest = read_manifest(cfg.assets_dir) or {}
    prov = make_provenance(cfg.root, config_hash=cfg_hash, assets_hash=manifest.get("overall_sha256"))

    # Golden vector: stable input
    golden_in = {"intent": "smoke", "v": 1}
    out = run_oracle(golden_in)

    result = {"provenance": prov.to_dict(), "input": golden_in, "output": out}
    # Persist to state dir for reproducibility
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    dump_file(str(cfg.state_dir / "smoke.latest.json"), result)
    print(dumps_stable(result))
    return 0


def acceptance_cmd() -> int:
    """Run acceptance suite (artifact-only) via shellable script."""
    repo_root = Path(__file__).resolve().parent.parent
    script = repo_root / "scripts" / "abx_acceptance.sh"
    if not script.exists():
        _cmd_err(f"Missing acceptance script: {script}")
        return 2
    proc = subprocess.run([str(script)], cwd=str(repo_root))
    return int(proc.returncode)

def up() -> int:
    """Start HTTP server (FastAPI if available, else minimal fallback)."""
    cfg = load_config()
    # Prefer FastAPI+uvicorn if installed; else fallback minhttp
    try:
        import uvicorn  # type: ignore
        from abx.server.app import build_app
        app = build_app()
        uvicorn.run(app, host=cfg.http_host, port=cfg.http_port, log_level=cfg.log_level.lower())
        return 0
    except ImportError:
        # fallback
        from abx.server.minhttp import serve
        serve()
        return 0

def drift_cmd(args: argparse.Namespace) -> int:
    """Handle drift detection subcommands."""
    if args.drift_action == "snapshot":
        s = take_snapshot()
        p = save_snapshot(s)
        _cmd_ok(f"Saved snapshot to {p}")
        print(dumps_stable(s.to_dict()))
        return 0

    if args.drift_action == "check":
        result = check_drift()
        print(dumps_stable(result))
        return 0 if result["ok"] else 1

    raise RuntimeError("unknown drift action")

def watchdog_cmd(args: argparse.Namespace) -> int:
    """Run watchdog loop (does not return under normal operation)."""
    watchdog_loop(
        ready_url=args.ready_url,
        unit_name=args.unit,
        interval_s=args.interval,
        fail_threshold=args.fail_threshold,
    )
    return 0

def update_cmd(args: argparse.Namespace) -> int:
    """Run atomic update with rollback."""
    result = update_atomic(repo_url=args.repo_url, branch=args.branch)
    print(dumps_stable(result))
    return 0 if result["ok"] else 1

def ingest_cmd(args: argparse.Namespace) -> int:
    """Run always-on Decodo ingestion scheduler."""
    jobs_path = os.environ.get("ABX_INGEST_JOBS", "/opt/aal/abraxas/.aal/jobs/ingest.jobs.json")
    interval_s = int(os.environ.get("ABX_INGEST_INTERVAL", "60"))
    run_ingest_forever(jobs_path, interval_s)
    return 0

def ui_cmd(args: argparse.Namespace) -> int:
    """Start chat-like UI server."""
    cfg = load_config()
    try:
        import uvicorn  # type: ignore
        app = build_ui_app()
        port = int(os.environ.get("ABX_UI_PORT", str(cfg.http_port)))
        uvicorn.run(app, host=cfg.http_host, port=port, log_level=cfg.log_level.lower())
        return 0
    except ImportError:
        _cmd_err("FastAPI/uvicorn not installed; install with: pip install fastapi uvicorn")
        return 2

def admin_cmd(args: argparse.Namespace) -> int:
    """Admin panel commands."""
    if args.admin_action == "handshake":
        result = admin_prompt()
        print(dumps_stable(result))
        return 0
    if args.admin_action == "up":
        from abx.admin.panel import run_up

        return run_up()
    if args.admin_action == "ingest":
        from abx.admin.panel import run_ingest

        if not args.path:
            _cmd_err("--path is required for admin ingest")
            return 2
        payload = {
            "path": args.path,
            "title": args.title,
            "source_type": args.source_type,
            "author": args.author,
            "date": args.date,
            "license_note": args.license_note,
            "tags": args.tags.split(",") if args.tags else [],
            "options": {},
        }
        return run_ingest(payload)
    if args.admin_action == "review":
        from abx.admin.panel import run_review

        return run_review()
    raise RuntimeError("unknown admin action")


def counterfactual_cmd(args: argparse.Namespace) -> int:
    """Run counterfactual replay engine."""
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.cli.counterfactual",
        git_hash="unknown",
    )
    result = invoke_capability(
        "replay.counterfactual.run_cli",
        {
            "portfolio": args.portfolio,
            "mask": args.mask,
            "run_id": args.run_id,
            "cases_dir": args.cases_dir,
            "portfolios_path": args.portfolios_path,
            "fdr_path": args.fdr_path,
            "overrides_path": args.overrides_path,
        },
        ctx=ctx,
        strict_execution=True,
    )
    for line in result.get("output_lines", []):
        print(line)
    return int(result.get("exit_code", 0))


def smv_cmd(args: argparse.Namespace) -> int:
    """Run signal marginal value analysis."""
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.cli.smv",
        git_hash="unknown",
    )
    result = invoke_capability(
        "value.smv.run_cli",
        {
            "portfolio": args.portfolio,
            "vector_map": args.vector_map,
            "allowlist_spec": args.allowlist_spec,
            "run_id": args.run_id,
            "cases_dir": args.cases_dir,
            "portfolios_path": args.portfolios_path,
            "max_units": args.max_units,
        },
        ctx=ctx,
        strict_execution=True,
    )
    for line in result.get("output_lines", []):
        print(line)
    return int(result.get("exit_code", 0))

def overlay_cmd(args: argparse.Namespace) -> int:
    """Handle overlay subcommands."""
    cfg = load_config()
    mgr = OverlayManager(cfg.overlays_dir, cfg.state_dir)

    if args.action == "list":
        print(dumps_stable({"overlays": mgr.list_overlays()}))
        return 0

    if args.action == "status":
        print(dumps_stable(mgr.status(args.name)))
        return 0

    if args.action == "install":
        # install from a manifest json string or file path
        import json
        if args.manifest_file:
            from abx.util.jsonutil import load_file
            d = load_file(args.manifest_file)
        else:
            d = json.loads(args.manifest_json)
        path = mgr.install(args.name, d)
        print(dumps_stable({"ok": True, "path": str(path)}))
        return 0

    if args.action == "start":
        print(dumps_stable(mgr.start(args.name)))
        return 0

    if args.action == "stop":
        print(dumps_stable(mgr.stop(args.name)))
        return 0

    raise RuntimeError("unknown action")

def main() -> None:
    """CLI entry point."""
    if len(sys.argv) > 1 and sys.argv[1] in {"aalmanac", "aalmanac-admin", "lens"}:
        from typer.main import get_command

        command = get_command(typer_app)
        command.main(args=sys.argv[1:], prog_name="abx")
        raise SystemExit(0)
    p = argparse.ArgumentParser(prog="abx", description="Abraxas Boot eXtensions")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_doctor = sub.add_parser("doctor", help="Check system readiness")
    p_doctor.add_argument("--level", default="standard", help="Diagnostic level")
    p_doctor.add_argument(
        "--full",
        action="store_true",
        help="Run full repo audit and emit audit_report.json",
    )
    p_doctor.add_argument(
        "--emit",
        type=str,
        default=None,
        help="Path to write audit report (default: data/audit_report.json)",
    )
    p_doctor.add_argument("--seed", type=int, default=None, help="Deterministic seed")
    sub.add_parser("up", help="Start HTTP server")
    sub.add_parser("smoke", help="Run smoke test")
    sub.add_parser("acceptance", help="Run acceptance suite (artifact-only)")

    p_assets = sub.add_parser("assets", help="Asset management")
    sub_assets = p_assets.add_subparsers(dest="assets_cmd", required=True)
    sub_assets.add_parser("sync", help="Generate asset manifest")

    p_ov = sub.add_parser("overlay", help="Overlay management")
    p_ov.add_argument("action", choices=["list", "status", "install", "start", "stop"])
    p_ov.add_argument("--name", default="")
    p_ov.add_argument("--manifest-file", default="")
    p_ov.add_argument("--manifest-json", default="")

    p_drift = sub.add_parser("drift", help="Drift detection")
    p_drift.add_argument("drift_action", choices=["snapshot", "check"], help="Drift action")

    p_wd = sub.add_parser("watchdog", help="Health monitoring with auto-restart")
    p_wd.add_argument("--ready-url", required=True, help="Health endpoint URL")
    p_wd.add_argument("--unit", required=True, help="Systemd unit name to restart")
    p_wd.add_argument("--interval", type=int, default=5, help="Check interval in seconds")
    p_wd.add_argument("--fail-threshold", type=int, default=3, help="Failures before restart")

    p_upd = sub.add_parser("update", help="Atomic update with rollback")
    p_upd.add_argument("--repo-url", required=True, help="Git repository URL")
    p_upd.add_argument("--branch", default="main", help="Git branch to clone")

    sub.add_parser("ingest", help="Run always-on Decodo ingestion scheduler")
    sub.add_parser("ui", help="Start chat-like UI server")
    p_admin = sub.add_parser("admin", help="Admin panel commands")
    p_admin.add_argument(
        "admin_action",
        nargs="?",
        default="handshake",
        choices=["handshake", "up", "ingest", "review"],
    )
    p_admin.add_argument("--path", default=None, help="Path to ingest file")
    p_admin.add_argument("--title", default="Untitled", help="Source title")
    p_admin.add_argument("--source-type", default="note", help="Source type")
    p_admin.add_argument("--author", default=None)
    p_admin.add_argument("--date", default=None)
    p_admin.add_argument("--license-note", default="local-only")
    p_admin.add_argument("--tags", default="")
    p_comp = sub.add_parser("compress", help="Run compression detection")
    p_comp.add_argument("--text", required=True, help="Input text event")
    p_comp.add_argument(
        "--lexicon-file",
        default=None,
        help="Path to lexicon JSON (list of canonical/variants)",
    )
    p_comp.add_argument("--domain", default="general", help="Domain label")
    p_comp.add_argument("--seed", type=int, default=None, help="Deterministic seed")

    p_cf = sub.add_parser("counterfactual", help="Run counterfactual replay")
    p_cf.add_argument("--portfolio", required=True, help="Portfolio ID")
    p_cf.add_argument(
        "--mask",
        action="append",
        default=[],
        help="Mask spec (repeatable)",
    )
    p_cf.add_argument("--run-id", default="counterfactual_manual")
    p_cf.add_argument("--cases-dir", default="data/backtests/cases")
    p_cf.add_argument(
        "--portfolios-path",
        default="data/backtests/portfolios/portfolios_v0_1.yaml",
    )
    p_cf.add_argument(
        "--fdr-path", default="data/forecast/decomposition/fdr_v0_1.yaml"
    )
    p_cf.add_argument("--overrides-path", default=None)

    p_smv = sub.add_parser("smv", help="Run signal marginal value analysis")
    p_smv.add_argument("--portfolio", required=True, help="Portfolio ID")
    p_smv.add_argument(
        "--vector-map",
        default="data/vector_maps/source_vector_map_v0_1.yaml",
    )
    p_smv.add_argument("--allowlist-spec", default=None)
    p_smv.add_argument("--run-id", default="smv_manual")
    p_smv.add_argument("--cases-dir", default="data/backtests/cases")
    p_smv.add_argument(
        "--portfolios-path",
        default="data/backtests/portfolios/portfolios_v0_1.yaml",
    )
    p_smv.add_argument("--max-units", type=int, default=25)

    p_self_heal = sub.add_parser("self-heal", help="Generate self-heal advisory plan")
    p_self_heal.add_argument(
        "--plan", action="store_true", help="Generate advisory plan only"
    )
    p_self_heal.add_argument(
        "--out", default="data/self_heal_plan.json", help="Plan output path"
    )
    p_self_heal.add_argument(
        "--audit",
        default="data/audit_report.json",
        help="Use this audit report as evidence",
    )

    p_govern = sub.add_parser("govern", help="Write governance receipt")
    p_govern.add_argument("--approve", action="store_true")
    p_govern.add_argument("--deny", action="store_true")
    p_govern.add_argument(
        "--rune",
        required=True,
        help="Action rune to approve/deny, e.g. actuator.apply",
    )
    p_govern.add_argument(
        "--plan",
        required=True,
        help="Path to plan json (e.g. data/self_heal_plan.json)",
    )
    p_govern.add_argument("--decided-by", default="daniel")
    p_govern.add_argument("--reason", default=None)

    p_apply = sub.add_parser("apply", help="Apply a governance-gated plan")
    p_apply.add_argument("--receipt", required=True, help="governance_receipt_id")
    p_apply.add_argument("--plan", required=True, help="Path to plan json")

    p_diag = sub.add_parser("diag", help="Diagnostics")
    p_diag.add_argument("diag_action", choices=["deps"], help="Diagnostic action")

    register_kite(sub)
    load_plugins(sub)

    args = p.parse_args()

    if args.cmd == "doctor":
        raise SystemExit(doctor(args))
    if args.cmd == "up":
        raise SystemExit(up())
    if args.cmd == "smoke":
        raise SystemExit(smoke())
    if args.cmd == "acceptance":
        raise SystemExit(acceptance_cmd())
    if args.cmd == "assets" and args.assets_cmd == "sync":
        raise SystemExit(assets_sync())
    if args.cmd == "overlay":
        # Normalize name requirement
        if args.action in ("status", "start", "stop", "install") and not args.name:
            _cmd_err("--name is required for this action")
            raise SystemExit(2)
        raise SystemExit(overlay_cmd(args))
    if args.cmd == "drift":
        raise SystemExit(drift_cmd(args))
    if args.cmd == "watchdog":
        raise SystemExit(watchdog_cmd(args))
    if args.cmd == "update":
        raise SystemExit(update_cmd(args))
    if args.cmd == "ingest":
        raise SystemExit(ingest_cmd(args))
    if args.cmd == "ui":
        raise SystemExit(ui_cmd(args))
    if args.cmd == "admin":
        raise SystemExit(admin_cmd(args))
    if args.cmd == "counterfactual":
        raise SystemExit(counterfactual_cmd(args))
    if args.cmd == "smv":
        raise SystemExit(smv_cmd(args))
    if args.cmd == "compress":
        raise SystemExit(compress_cmd(args))
    if args.cmd == "self-heal":
        raise SystemExit(self_heal_cmd(args))
    if args.cmd == "govern":
        raise SystemExit(govern_cmd(args))
    if args.cmd == "apply":
        raise SystemExit(apply_cmd(args))
    if args.cmd == "diag":
        raise SystemExit(diag_cmd(args))

if __name__ == "__main__":
    main()
