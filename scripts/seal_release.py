#!/usr/bin/env python3
"""
Abraxas Seal Release — Deterministic release validation script.

Usage:
  python -m scripts.seal_release --run_id seal
  python -m scripts.seal_release --run_id seal --tick 0 --runs 12

Steps:
  1) Run one tick into ./artifacts_seal
  2) Validate emitted artifacts against schemas
  3) Run dozen-run gate into ./artifacts_gate (12 runs)
  4) Write SealReport.v0 JSON with paths/hashes and pass/fail

Exit code:
  0 if validation AND gate pass
  1 otherwise
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Import Abraxas runtime
from abraxas.runtime.tick import abraxas_tick
from abraxas.runtime.invariance_gate import dozen_run_tick_invariance_gate


def _read_version(repo_root: Path) -> str:
    """Read VERSION file."""
    version_file = repo_root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _read_version_pack(repo_root: Path) -> Dict[str, Any]:
    """Read abx_versions.json."""
    vp_file = repo_root / "abx_versions.json"
    if vp_file.exists():
        return json.loads(vp_file.read_text(encoding="utf-8"))
    return {"schema": "AbraxasVersionPack.v0", "abraxas": "0.0.0"}


def _stable_json_bytes(obj: Any) -> bytes:
    """Serialize object to deterministic JSON bytes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    """Compute SHA-256 hex digest."""
    import hashlib
    return hashlib.sha256(data).hexdigest()


def _safe_clear_dir(path: Path) -> None:
    """Safely remove and recreate a directory."""
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def run_seal_tick(
    artifacts_dir: str,
    run_id: str,
    tick: int,
) -> Dict[str, Any]:
    """
    Run a single deterministic tick for sealing.
    Uses minimal deterministic inputs.
    """
    # Deterministic pipeline functions for seal
    def run_signal(ctx):
        return {"signal": 1}

    def run_compress(ctx):
        return {"compress": 1}

    def run_overlay(ctx):
        return {"overlay": 1}

    return abraxas_tick(
        tick=tick,
        run_id=run_id,
        mode="sandbox",
        context={"x": 1},
        artifacts_dir=artifacts_dir,
        run_signal=run_signal,
        run_compress=run_compress,
        run_overlay=run_overlay,
        run_shadow_tasks={"sei": lambda ctx: {"sei": 0}},
    )


def run_validation(
    artifacts_dir: str,
    run_id: str,
    tick: int,
    schemas_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Run artifact validation."""
    # Import here to avoid circular imports
    from scripts.validate_artifacts import validate_run

    return validate_run(
        artifacts_dir=artifacts_dir,
        run_id=run_id,
        tick=tick,
        schemas_dir=schemas_dir,
    )


def run_dozen_gate(
    base_artifacts_dir: str,
    run_id: str,
    tick: int,
    runs: int,
) -> Dict[str, Any]:
    """Run dozen-run invariance gate."""

    def run_once(i: int, artifacts_dir: str) -> Dict[str, Any]:
        return run_seal_tick(artifacts_dir, run_id, tick)

    result = dozen_run_tick_invariance_gate(
        base_artifacts_dir=base_artifacts_dir,
        runs=runs,
        run_once=run_once,
    )

    return {
        "ok": result.ok,
        "expected_trendpack_sha256": result.expected_sha256,
        "trendpack_sha256s": result.sha256s,
        "expected_runheader_sha256": result.expected_runheader_sha256,
        "runheader_sha256s": result.runheader_sha256s,
        "first_mismatch_run": result.first_mismatch_run,
        "divergence_kind": result.divergence.get("kind") if result.divergence else None,
        "divergence": result.divergence,
    }


def write_seal_report(
    artifacts_dir: str,
    run_id: str,
    version: str,
    version_pack: Dict[str, Any],
    seal_tick_artifacts: Dict[str, Any],
    validation_result: Dict[str, Any],
    dozen_gate_result: Dict[str, Any],
) -> tuple[str, str]:
    """Write SealReport.v0 artifact."""
    ok = validation_result.get("ok", False) and dozen_gate_result.get("ok", False)

    report = {
        "schema": "SealReport.v0",
        "version": version,
        "version_pack": version_pack,
        "seal_tick_artifacts": seal_tick_artifacts,
        "validation_result": {
            "ok": validation_result.get("ok"),
            "validated_ticks": validation_result.get("validated_ticks", []),
            "failures": validation_result.get("failures", []),
        },
        "dozen_gate_result": {
            "ok": dozen_gate_result.get("ok"),
            "expected_trendpack_sha256": dozen_gate_result.get("expected_trendpack_sha256"),
            "expected_runheader_sha256": dozen_gate_result.get("expected_runheader_sha256"),
            "first_mismatch_run": dozen_gate_result.get("first_mismatch_run"),
            "divergence_kind": dozen_gate_result.get("divergence_kind"),
        },
        "ok": ok,
    }

    # Write deterministically
    report_bytes = _stable_json_bytes(report)
    report_sha = _sha256_hex(report_bytes)

    runs_dir = Path(artifacts_dir) / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    report_path = runs_dir / f"{run_id}.sealreport.json"
    report_path.write_bytes(report_bytes)

    return str(report_path), report_sha


def main() -> int:
    repo_root = Path(__file__).parent.parent
    
    ap = argparse.ArgumentParser(description="Seal Abraxas release")
    ap.add_argument("--version", default=None, help="Version (default: read from VERSION)")
    ap.add_argument("--run_id", default="seal", help="Run ID (default: seal)")
    ap.add_argument("--tick", type=int, default=0, help="Tick number (default: 0)")
    ap.add_argument("--runs", type=int, default=12, help="Number of gate runs (default: 12)")
    ap.add_argument("--schemas_dir", default=None, help="Schemas directory")
    args = ap.parse_args()

    version = args.version or _read_version(repo_root)
    version_pack = _read_version_pack(repo_root)
    schemas_dir = args.schemas_dir or str(repo_root / "schemas")

    print(f"=" * 60)
    print(f"ABRAXAS SEAL RELEASE v{version}")
    print(f"=" * 60)
    print()

    # Directories
    seal_dir = Path("./artifacts_seal")
    gate_dir = Path("./artifacts_gate")

    # Step 1: Clear and run seal tick
    print(f"[1/4] Running seal tick into {seal_dir}...")
    _safe_clear_dir(seal_dir)

    tick_out = run_seal_tick(str(seal_dir), args.run_id, args.tick)
    artifacts = tick_out.get("artifacts", {})

    print(f"  TrendPack: {artifacts.get('trendpack')}")
    print(f"  ResultsPack: {artifacts.get('results_pack')}")
    print(f"  ViewPack: {artifacts.get('viewpack')}")
    print(f"  RunIndex: {artifacts.get('runindex')}")
    print(f"  RunHeader: {artifacts.get('run_header')}")
    print()

    # Verify all required artifacts are present
    required_keys = ["trendpack", "trendpack_sha256", "results_pack", "results_pack_sha256",
                     "runindex", "runindex_sha256", "viewpack", "viewpack_sha256",
                     "run_header", "run_header_sha256"]
    missing = [k for k in required_keys if not artifacts.get(k)]
    if missing:
        print(f"ERROR: Missing required artifacts: {missing}")
        return 1

    # Step 2: Validate artifacts
    print(f"[2/4] Validating artifacts...")
    validation_result = run_validation(str(seal_dir), args.run_id, args.tick, schemas_dir)
    
    if validation_result["ok"]:
        print(f"  VALIDATION: PASS")
        print(f"  Validated ticks: {validation_result['validated_ticks']}")
    else:
        print(f"  VALIDATION: FAIL")
        for f in validation_result.get("failures", []):
            print(f"    - {f['artifact_kind']}: {f['errors']}")
    print()

    # Step 3: Run dozen-run gate
    print(f"[3/4] Running dozen-run gate ({args.runs} runs) into {gate_dir}...")
    _safe_clear_dir(gate_dir)

    gate_result = run_dozen_gate(str(gate_dir), args.run_id, args.tick, args.runs)

    if gate_result["ok"]:
        print(f"  GATE: PASS")
        print(f"  TrendPack SHA: {gate_result['expected_trendpack_sha256'][:16]}...")
        print(f"  RunHeader SHA: {gate_result['expected_runheader_sha256'][:16] if gate_result['expected_runheader_sha256'] else 'N/A'}...")
    else:
        print(f"  GATE: FAIL")
        print(f"  First mismatch run: {gate_result['first_mismatch_run']}")
        print(f"  Divergence kind: {gate_result['divergence_kind']}")
    print()

    # Step 4: Write SealReport
    print(f"[4/4] Writing SealReport.v0...")
    report_path, report_sha = write_seal_report(
        artifacts_dir=str(seal_dir),
        run_id=args.run_id,
        version=version,
        version_pack=version_pack,
        seal_tick_artifacts=artifacts,
        validation_result=validation_result,
        dozen_gate_result=gate_result,
    )

    print(f"  Path: {report_path}")
    print(f"  SHA256: {report_sha[:16]}...")
    print()

    # Final result
    ok = validation_result["ok"] and gate_result["ok"]
    print(f"=" * 60)
    if ok:
        print(f"SEAL RELEASE: PASS")
        print()
        print("Artifacts created:")
        print(f"  {seal_dir}/")
        print(f"    runs/{args.run_id}.sealreport.json")
        print(f"    runs/{args.run_id}.runheader.json")
        print(f"    run_index/{args.run_id}/{args.tick:06d}.runindex.json")
        print(f"    viz/{args.run_id}/{args.tick:06d}.trendpack.json")
        print(f"    results/{args.run_id}/{args.tick:06d}.resultspack.json")
        print(f"    view/{args.run_id}/{args.tick:06d}.viewpack.json")
    else:
        print(f"SEAL RELEASE: FAIL")
        if not validation_result["ok"]:
            print("  - Validation failed")
        if not gate_result["ok"]:
            print("  - Dozen-run gate failed")
    print(f"=" * 60)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
