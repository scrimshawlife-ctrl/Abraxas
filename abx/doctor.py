"""ABX doctor diagnostics for Orin readiness."""

from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
from pathlib import Path
from typing import Any

from abx.runtime.config import load_config
from shared.policy import load_policy

REPO_ROOT = Path(__file__).resolve().parents[1]


def _port_free(host: str, port: int) -> bool:
    """Check if port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            return sock.connect_ex((host, port)) != 0
    except Exception:
        return True


def _run_audit(out_path: str | None = None) -> str:
    """
    Runs tools/audit_repo.py and returns the path to data/audit_report.json
    (or custom emit path).
    """
    audit_py = REPO_ROOT / "tools" / "audit_repo.py"
    if not audit_py.exists():
        raise FileNotFoundError(f"Missing: {audit_py}")

    output = subprocess.check_output(
        ["python3", str(audit_py)], cwd=str(REPO_ROOT)
    ).decode().strip()
    default_path = Path(output)

    if out_path:
        emit_path = Path(out_path)
        if not emit_path.is_absolute():
            emit_path = REPO_ROOT / emit_path
        emit_path.parent.mkdir(parents=True, exist_ok=True)
        emit_path.write_bytes(default_path.read_bytes())
        return str(emit_path)

    return str(default_path)


def _run_migration_queue() -> str:
    """Produces data/migration_queue.json from audit + rune invocation ledger."""
    mq_py = REPO_ROOT / "tools" / "summarize_migration_queue.py"
    if not mq_py.exists():
        raise FileNotFoundError(f"Missing: {mq_py}")
    output = subprocess.check_output(
        ["python3", str(mq_py)], cwd=str(REPO_ROOT)
    ).decode().strip()
    return output


def _run_patch_suggestions() -> str:
    ps_py = REPO_ROOT / "tools" / "generate_patch_suggestions.py"
    if not ps_py.exists():
        raise FileNotFoundError(f"Missing: {ps_py}")
    output = subprocess.check_output(
        ["python3", str(ps_py)], cwd=str(REPO_ROOT)
    ).decode().strip()
    return output


def _run_schema_gen() -> str:
    sg_py = REPO_ROOT / "tools" / "generate_schema_registry.py"
    if not sg_py.exists():
        raise FileNotFoundError(f"Missing: {sg_py}")
    output = subprocess.check_output(
        ["python3", str(sg_py)], cwd=str(REPO_ROOT)
    ).decode().strip()
    return output


def _print_migration_queue(mq_path: str) -> None:
    data = json.loads(Path(mq_path).read_text(encoding="utf-8"))
    print("=== MIGRATION QUEUE (top) ===")
    for index, item in enumerate(data.get("migration_queue", [])[:10], start=1):
        file = item.get("file", "?")
        line = item.get("line", "?")
        item_type = item.get("type", "?")
        symbol = item.get("symbol", "")
        print(f"{index}. [{item_type}] {file}:{line}  {symbol}")
    print("\nTop runes:", data.get("top_runes", []))
    print("Top callsites:", data.get("top_callsites", []))
    print(f"\nmigration_queue: {mq_path}")
    print("=============================\n")

def _print_audit_summary(audit_path: str) -> dict[str, Any]:
    data = json.loads(Path(audit_path).read_text(encoding="utf-8"))
    scores = data.get("scores", {})
    repo = data.get("repo", {})
    findings = data.get("findings", {})
    policy_doc = load_policy()
    coupling = policy_doc.get("coupling", {}) or {}
    print("\n=== ABRAXAS CANON AUDIT (summary) ===")
    print(f"commit: {repo.get('commit')}")
    print(f"dirty:  {repo.get('dirty')}")
    print(f"rune_coverage_pct:          {scores.get('rune_coverage_pct')}")
    print(f"rune_invoke_ratio:          {scores.get('rune_invoke_ratio')}")
    print(f"hidden_coupling_count:      {scores.get('hidden_coupling_count')}")
    print(f"side_effect_count:          {scores.get('side_effect_count')}")
    print(f"detector_purity_violations: {scores.get('detector_purity_violations')}")
    print(f"forbidden_actuation_count:  {scores.get('forbidden_actuation_count')}")
    print(
        "cross_boundary_import_count:"
        f"{scores.get('cross_boundary_import_count')}"
    )
    print(f"\naudit_report: {audit_path}")
    print("=====================================\n")
    if int(scores.get("forbidden_actuation_count") or 0) > 0:
        offenders = (findings.get("forbidden_actuation") or [])[:10]
        print("FAIL: Forbidden actuation detected outside infra/actuator.py")
        for offender in offenders:
            print(
                f"- {offender.get('file')}:{offender.get('line')} "
                f"[{offender.get('kind')}] {offender.get('symbol')}"
            )
        raise SystemExit(2)

    max_cross = int(coupling.get("max_cross_boundary_imports", 0))
    cross_count = int(scores.get("cross_boundary_import_count") or 0)
    if cross_count > max_cross:
        offenders = (findings.get("cross_boundary_imports") or [])[:10]
        print(
            "FAIL: Cross-boundary imports detected "
            f"({cross_count} > allowed {max_cross})"
        )
        for offender in offenders:
            print(
                f"- {offender.get('file')}:{offender.get('line')} "
                f"{offender.get('from')}→{offender.get('to')} "
                f"{offender.get('symbol')}"
            )
        raise SystemExit(3)

    min_ratio = float(coupling.get("min_rune_invoke_ratio", 0.70))
    ratio = float(scores.get("rune_invoke_ratio") or 0.0)
    if ratio < min_ratio:
        print(
            "FAIL: rune_invoke_ratio too low "
            f"({ratio:.3f} < required {min_ratio:.3f})"
        )
        print(
            "Remedy: route cross-module operations through "
            "kernel.invoke(rune_id, ...) and remove direct imports."
        )
        raise SystemExit(4)
    return {
        "rune_coverage_pct": scores.get("rune_coverage_pct"),
        "hidden_coupling_count": scores.get("hidden_coupling_count"),
        "side_effect_count": scores.get("side_effect_count"),
        "detector_purity_violations": scores.get(
            "detector_purity_violations"
        ),
    }


def run_doctor(payload: dict[str, Any]) -> dict[str, Any]:
    """Run system diagnostics and readiness checks."""
    if payload.get("full"):
        audit_path = _run_audit(out_path=payload.get("emit"))
        summary = _print_audit_summary(audit_path)
        mq_path = _run_migration_queue()
        _print_migration_queue(mq_path)
        ps_index = _run_patch_suggestions()
        print(f"patch_suggestions_index: {ps_index}\n")
        sg_path = _run_schema_gen()
        print(f"schema_registry_gen: {sg_path}\n")
        return {
            "ok": True,
            "audit_report": audit_path,
            "migration_queue": mq_path,
            "patch_suggestions_index": ps_index,
            "schema_registry_gen": sg_path,
            "summary": summary,
            "diagnostic_level": payload.get("diagnostic_level"),
        }

    cfg = load_config()
    issues: list[str] = []

    arch = platform.machine().lower()
    if arch not in ("aarch64", "arm64", "x86_64", "amd64"):
        issues.append(f"unknown_arch:{arch}")

    # JetPack hint
    jetpack = os.environ.get("JETPACK_VERSION")
    # CUDA presence (best-effort)
    cuda_ok = Path("/usr/local/cuda").exists()

    # dirs
    for directory in [cfg.root, cfg.assets_dir, cfg.overlays_dir, cfg.state_dir]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            issues.append(f"mkdir:{directory}:{exc}")

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
        "diagnostic_level": payload.get("diagnostic_level"),
    }
    return report
