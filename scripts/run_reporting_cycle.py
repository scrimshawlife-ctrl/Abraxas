from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from abx.gap_closure_invariance import read_gap_closure_invariance_payload
from abx.promotion_preflight import read_promotion_preflight
from abx.readiness_comparison import read_latest_comparison
from abx.report_freshness import evaluate_freshness
from abx.reporting_cycle import (
    LATEST_PATH,
    cycle_id_from_payload,
    derive_overall_status,
    normalize_step_status,
    now_utc,
)


def _run_step(command: list[str]) -> int:
    completed = subprocess.run(command, cwd=ROOT, check=False)
    return int(completed.returncode)


def _read_developer_status(path: Path) -> str:
    if not path.exists():
        return "NOT_COMPUTABLE"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return normalize_step_status(str(payload.get("status", "NOT_COMPUTABLE")))


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    commands: list[tuple[str, list[str]]] = [
        ("developer_readiness", ["python", "scripts/run_developer_readiness.py"]),
        ("gap_closure_invariance", ["python", "scripts/project_gap_closure_invariance.py"]),
        ("readiness_comparison", ["python", "scripts/log_readiness_comparison.py"]),
        ("promotion_preflight", ["python", "scripts/generate_promotion_preflight.py"]),
    ]

    return_codes: dict[str, int] = {}
    for step_name, command in commands:
        return_codes[step_name] = _run_step(command)

    developer_path = ROOT / "out" / "reports" / "developer_readiness.json"
    invariance_path = ROOT / "out" / "reports" / "gap_closure_invariance.projection.json"
    comparison_path = ROOT / "out" / "reports" / "readiness_comparison.latest.json"
    advisory_path = ROOT / "out" / "reports" / "promotion_preflight.latest.json"

    missing_artifacts = sorted(
        path.as_posix()
        for path in [developer_path, invariance_path, comparison_path, advisory_path]
        if not path.exists()
    )

    invariance_payload = read_gap_closure_invariance_payload(invariance_path)
    comparison_payload = read_latest_comparison(comparison_path)
    advisory_payload = read_promotion_preflight(advisory_path)

    steps = {
        "developer_readiness_status": _read_developer_status(developer_path),
        "invariance_status": normalize_step_status(str(invariance_payload.get("status", "NOT_COMPUTABLE"))),
        "comparison_status": normalize_step_status(str(comparison_payload.get("status", "NOT_COMPUTABLE")), ok_values={"OK"}),
        "advisory_status": normalize_step_status(str(advisory_payload.get("status", "NOT_COMPUTABLE")), ok_values={"OK"}),
    }

    overall_status = derive_overall_status(steps=steps, missing_artifacts=missing_artifacts)
    timestamp_utc = now_utc()
    developer_raw = _read_json(developer_path) or {}
    invariance_raw = _read_json(invariance_path) or {}
    comparison_raw = (comparison_payload.get("comparison") if isinstance(comparison_payload.get("comparison"), dict) else {}) or {}
    advisory_raw = (advisory_payload.get("advisory") if isinstance(advisory_payload.get("advisory"), dict) else {}) or {}

    per_step_freshness = {
        "developer_readiness": evaluate_freshness(
            developer_raw.get("timestamp_utc"),
            timestamp_utc,
            artifact_type="developer_readiness",
        ),
        "invariance": evaluate_freshness(
            ((invariance_raw.get("provenance") if isinstance(invariance_raw.get("provenance"), dict) else {}).get("projection_generated_at")),
            timestamp_utc,
            artifact_type="invariance",
        ),
        "comparison": evaluate_freshness(
            comparison_raw.get("timestamp_utc"),
            timestamp_utc,
            artifact_type="comparison",
        ),
        "preflight": evaluate_freshness(
            advisory_raw.get("timestamp_utc"),
            timestamp_utc,
            artifact_type="preflight",
        ),
    }
    reporting_cycle_freshness = evaluate_freshness(
        timestamp_utc,
        timestamp_utc,
        artifact_type="reporting_cycle",
    )
    cycle = {
        "cycle_id": cycle_id_from_payload(
            timestamp_utc=timestamp_utc,
            steps=steps,
            overall_status=overall_status,
            missing_artifacts=missing_artifacts,
        ),
        "timestamp_utc": timestamp_utc,
        "steps": steps,
        "overall_status": overall_status,
        "missing_artifacts": missing_artifacts,
        "freshness": {
            "per_step": per_step_freshness,
            "reporting_cycle": reporting_cycle_freshness,
            "overall_stale": any(bool(item.get("is_stale")) for item in per_step_freshness.values()),
        },
        "provenance": {
            "source": "scripts/run_reporting_cycle.py",
            "deterministic_ordering": [
                "cycle_id",
                "timestamp_utc",
                "steps",
                "overall_status",
                "missing_artifacts",
                "provenance",
            ],
            "execution_order": [name for name, _ in commands],
            "step_return_codes": {k: return_codes[k] for k in sorted(return_codes.keys())},
        },
    }

    LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_PATH.write_text(json.dumps(cycle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"cycle_id": cycle["cycle_id"], "overall_status": cycle["overall_status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
