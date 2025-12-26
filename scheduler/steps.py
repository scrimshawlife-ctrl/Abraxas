"""
Scheduler Steps
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from abraxas.acquire.dap_builder import DapInputs, build_dap
from abraxas.evolve.epp_builder import build_epp


def run_step_build_dap(run_context: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    run_id = run_context.get("run_id", "manual")
    ts = datetime.now(timezone.utc).isoformat()
    inputs = DapInputs(
        forecast_scores_path=args.get("forecast_scores_path"),
        regime_scores_path=args.get("regime_scores_path"),
        component_scores_path=args.get("component_scores_path"),
        drift_report_path=args.get("drift_report_path"),
        smv_report_path=args.get("smv_report_path"),
        integrity_snapshot_path=args.get("integrity_snapshot_path"),
    )
    json_path, _ = build_dap(
        run_id=run_id,
        out_dir=args.get("reports_dir", "out/reports"),
        playbook_path=args.get("playbook_path", "data/acquire/acquisition_playbook_v0_1.yaml"),
        inputs=inputs,
        ts=ts,
    )
    return {"plan_path": json_path}


def run_step_build_epp(run_context: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    run_id = run_context.get("run_id", "manual")
    json_path, md_path = build_epp(
        run_id=run_id,
        out_dir=args.get("reports_dir", "out/reports"),
        inputs_dir=args.get("reports_dir", "out/reports"),
        osh_ledger_path=args.get("osh_ledger", "out/osh_ledgers/fetch_artifacts.jsonl"),
        integrity_snapshot_path=args.get("integrity_snapshot_path"),
        dap_path=args.get("dap_path"),
        ledger_path=args.get("ledger_path", "out/value_ledgers/epp_runs.jsonl"),
    )
    return {"epp_json": json_path, "epp_md": md_path}
