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
- log: Deterministic logging operations (append/compact/vacuum/verify)
"""

from __future__ import annotations
import argparse
import os
import platform
import socket
import sys
from pathlib import Path
from typing import Any, Dict

from abx.runtime.config import load_config
from abx.assets.manifest import write_manifest, read_manifest
from abx.runtime.provenance import make_provenance, compute_config_hash
from abx.core.pipeline import run_oracle
from abx.util.jsonutil import dumps_stable, dump_file
from abx.overlays.manager import OverlayManager
from abx.runtime.drift import take_snapshot, save_snapshot, check_drift
from abx.runtime.watchdog import watchdog_loop
from abx.runtime.updater import update_atomic
from abx.ingest.scheduler import run_ingest_forever
from abx.ui.server import build_ui_app
from abx.ui.admin_handshake import admin_prompt
from abx.store.sqlite_store import connect
from abx.log import ledger, compactor, policy

def _cmd_ok(msg: str) -> None:
    """Print success message."""
    print(msg)

def _cmd_err(msg: str) -> None:
    """Print error message to stderr."""
    print(msg, file=sys.stderr)

def _port_free(host: str, port: int) -> bool:
    """Check if port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex((host, port)) != 0
    except Exception:
        return True

def doctor() -> int:
    """Run system diagnostics and readiness checks."""
    cfg = load_config()
    issues = []

    arch = platform.machine().lower()
    if arch not in ("aarch64", "arm64", "x86_64", "amd64"):
        issues.append(f"unknown_arch:{arch}")

    # JetPack hint
    jetpack = os.environ.get("JETPACK_VERSION")
    # CUDA presence (best-effort)
    cuda_ok = Path("/usr/local/cuda").exists()

    # dirs
    for d in [cfg.root, cfg.assets_dir, cfg.overlays_dir, cfg.state_dir]:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"mkdir:{d}:{e}")

    # port
    if not _port_free(cfg.http_host, cfg.http_port):
        issues.append(f"port_in_use:{cfg.http_host}:{cfg.http_port}")

    report = {
        "ok": len(issues) == 0,
        "arch": arch,
        "jetpack_env": jetpack,
        "cuda_dir_present": cuda_ok,
        "root": str(cfg.root),
        "assets_dir": str(cfg.assets_dir),
        "overlays_dir": str(cfg.overlays_dir),
        "state_dir": str(cfg.state_dir),
        "http": [cfg.http_host, cfg.http_port],
        "issues": issues,
    }
    print(dumps_stable(report))
    return 0 if report["ok"] else 2

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
    """Print admin handshake (module discovery)."""
    result = admin_prompt()
    print(dumps_stable(result))
    return 0

def log_cmd(args: argparse.Namespace) -> int:
    """Handle log subcommands."""
    con = connect()
    ledger.init_ledger(con)
    compactor.init_compactor_tables(con)

    if args.log_action == "append":
        # Development command to append a test event
        event_id = ledger.append_event(
            con,
            kind=args.kind or "test",
            module=args.module or "cli",
            frame_id=args.frame_id or "",
            payload={"message": args.message or "test event"}
        )
        _cmd_ok(f"Appended event {event_id}")
        return 0

    if args.log_action == "compact":
        # Compact events
        stats = ledger.get_stats(con)
        if stats["total_events"] == 0:
            _cmd_ok("No events to compact")
            return 0

        # Use policy to calculate range
        comp_range = policy.calculate_compaction_range(stats)
        if comp_range is None:
            _cmd_ok(f"Not enough events to compact (have {stats['total_events']}, need {policy.COMPACT_INTERVAL_EVENTS})")
            return 0

        start_id, end_id = comp_range
        segment_id = compactor.compact(con, start_id, end_id, top_k=policy.DICT_TOPK)

        segment = compactor.get_segment(con, segment_id)
        _cmd_ok(f"Compacted events [{start_id}, {end_id}] -> segment {segment_id}")
        print(dumps_stable(segment))
        return 0

    if args.log_action == "vacuum":
        # Vacuum old events based on retention policy
        cutoff_ts = policy.get_vacuum_cutoff_ts()

        # Count events to vacuum
        cur = con.execute("SELECT COUNT(*) FROM log_events WHERE ts < ?;", (cutoff_ts,))
        count = cur.fetchone()[0]

        if count == 0:
            _cmd_ok("No events to vacuum")
            return 0

        # Delete old events
        con.execute("DELETE FROM log_events WHERE ts < ?;", (cutoff_ts,))
        con.commit()

        _cmd_ok(f"Vacuumed {count} events older than retention period")
        return 0

    if args.log_action == "verify":
        # Verify hash chain integrity
        result = ledger.verify_chain(con)
        print(dumps_stable(result))
        return 0 if result["ok"] else 1

    if args.log_action == "stats":
        # Show ledger statistics
        stats = ledger.get_stats(con)
        segments = compactor.list_segments(con)
        result = {
            "ledger": stats,
            "segments": segments,
        }
        print(dumps_stable(result))
        return 0

    raise RuntimeError("unknown log action")

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
    p = argparse.ArgumentParser(prog="abx", description="Abraxas Boot eXtensions")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Check system readiness")
    sub.add_parser("up", help="Start HTTP server")
    sub.add_parser("smoke", help="Run smoke test")

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
    sub.add_parser("admin", help="Print admin handshake (module discovery)")

    p_log = sub.add_parser("log", help="Deterministic logging operations")
    p_log.add_argument("log_action", choices=["append", "compact", "vacuum", "verify", "stats"], help="Log action")
    p_log.add_argument("--kind", default="", help="Event kind (for append)")
    p_log.add_argument("--module", default="", help="Module name (for append)")
    p_log.add_argument("--frame-id", default="", help="Frame ID (for append)")
    p_log.add_argument("--message", default="", help="Event message (for append)")

    args = p.parse_args()

    if args.cmd == "doctor":
        raise SystemExit(doctor())
    if args.cmd == "up":
        raise SystemExit(up())
    if args.cmd == "smoke":
        raise SystemExit(smoke())
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
    if args.cmd == "log":
        raise SystemExit(log_cmd(args))

if __name__ == "__main__":
    main()
