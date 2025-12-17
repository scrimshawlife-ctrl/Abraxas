"""ABX CLI - Abraxas Boot eXtensions command-line interface.

Subcommands:
- doctor: Check system readiness for Orin deployment
- up: Start HTTP server with health endpoints
- smoke: Run deterministic smoke test
- assets sync: Generate asset manifest
- overlay: Manage overlay lifecycle (list/status/install/start/stop)
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

if __name__ == "__main__":
    main()
