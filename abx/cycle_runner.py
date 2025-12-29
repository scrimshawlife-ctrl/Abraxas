from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _write_json(path: str, obj: Dict[str, Any]) -> None:
    _ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _cmd_ok(code: int) -> bool:
    return int(code) == 0


def _run(cmd: List[str]) -> Tuple[int, str]:
    try:
        p = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        return int(p.returncode), str(p.stdout or "")
    except Exception as e:
        return 127, f"EXCEPTION: {e}"


def _step(log: List[Dict[str, Any]], name: str, cmd: List[str]) -> bool:
    ts = _utc_now_iso()
    code, out = _run(cmd)
    ok = _cmd_ok(code)
    log.append(
        {
            "ts": ts,
            "step": name,
            "cmd": cmd,
            "code": code,
            "ok": ok,
            "output": out[-8000:],
        }
    )
    return ok


def _module_exists(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _run_module(
    log: List[Dict[str, Any]], name: str, module: str, args: List[str]
) -> bool:
    if not _module_exists(module):
        log.append(
            {
                "ts": _utc_now_iso(),
                "step": name,
                "module": module,
                "skipped": True,
                "reason": "module_missing",
            }
        )
        return False
    return _step(log, name, ["python", "-m", module, *args])


def main() -> int:
    ap = argparse.ArgumentParser(description="WO-86: One-command Abraxas cycle runner")
    ap.add_argument("--run-id", required=True, help="Run identifier for ledgers")
    ap.add_argument("--reports-dir", default="out/reports")
    ap.add_argument("--outbox", default="out/reports/review_tasks.json")
    ap.add_argument("--cycle-log", default="")
    ap.add_argument("--max-due", type=int, default=10)
    ap.add_argument(
        "--skip-acquire", action="store_true", help="Skip acquisition/resolution steps"
    )
    ap.add_argument("--provider", default="", help="Preferred provider (decodo/requests/etc)")
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cycle_log_path = args.cycle_log or os.path.join(
        args.reports_dir, f"cycle_runner_{stamp}.json"
    )
    _ensure_dir(args.reports_dir)

    log: List[Dict[str, Any]] = []
    meta = {
        "version": "cycle_runner.v0.1",
        "ts": _utc_now_iso(),
        "run_id": args.run_id,
        "notes": "WO-86 orchestrates metrics->pollution->review->acquisition->resolution->recompute->attribution.",
    }

    _run_module(log, "evidence_metrics(pre)", "abx.evidence_metrics", [])
    _run_module(log, "time_to_truth(pre)", "abx.claim_timeseries", [])
    _run_module(log, "proof_integrity(pre)", "abx.proof_integrity", [])

    _run_module(log, "truth_pollution", "abx.truth_pollution", [])
    _run_module(log, "slang_extract", "abx.slang_extract", ["--run-id", args.run_id])
    _run_module(log, "slang_migration", "abx.slang_migration", [])
    _run_module(log, "aalmanac_promote", "abx.aalmanac", ["--run-id", args.run_id])
    _run_module(log, "mimetic_weather", "abx.mimetic_weather", [])
    _run_module(
        log, "weather_to_tasks", "abx.weather_to_tasks", ["--run-id", args.run_id]
    )
    _run_module(
        log, "term_claim_binder", "abx.term_claim_binder", ["--run-id", args.run_id]
    )
    _run_module(log, "forecast_review_state", "abx.forecast_review_state", [])

    _run_module(
        log,
        "review_scheduler",
        "abx.review_scheduler",
        [
            "--run-id",
            args.run_id,
            "--outbox",
            args.outbox,
            "--max-due",
            str(int(args.max_due)),
        ],
    )

    _run_module(log, "task_union_ledger", "abx.task_union_ledger", ["--run-id", args.run_id])

    import glob

    batches = sorted(glob.glob("out/reports/acq_batch_*.json"))
    acq_in = batches[-1] if batches else ""
    outbox = _read_json(acq_in) if acq_in else {"tasks": []}
    tasks = outbox.get("tasks") if isinstance(outbox.get("tasks"), list) else []
    n_tasks = len(tasks)
    log.append(
        {
            "ts": _utc_now_iso(),
            "step": "acq_batch_summary",
            "n_tasks": n_tasks,
            "acq_in": acq_in,
        }
    )

    if (not args.skip_acquire) and n_tasks > 0 and acq_in:
        _run_module(
            log,
            "anchor_url_resolver",
            "abx.anchor_url_resolver",
            ["--run-id", args.run_id, "--in", acq_in],
        )

        import glob

        resolved = sorted(glob.glob("out/batches/acq_batch_resolved_*.json"))
        acq_in_resolved = resolved[-1] if resolved else acq_in

        media_args = [
            "--run-id",
            args.run_id,
            "--in",
            acq_in_resolved,
            "--provider",
            args.provider,
        ]
        _run_module(log, "media_origin_verify", "abx.media_origin_verify", media_args)

        import glob

        mors = sorted(glob.glob("out/reports/media_origin_verify_*.json"))
        mor = mors[-1] if mors else ""

        acq_args = ["--run-id", args.run_id, "--in", acq_in_resolved]
        if args.provider:
            acq_args += ["--provider", args.provider]
        if mor:
            acq_args += ["--media-origin-report", mor]
        _run_module(log, "acquisition_execute", "abx.acquisition_execute", acq_args)

        res_args = ["--run-id", args.run_id]
        if args.provider:
            res_args += ["--provider", args.provider]
        _run_module(log, "online_resolver", "abx.online_resolver", res_args)
        _run_module(
            log, "reupload_storm_detector", "abx.reupload_storm_detector", ["--run-id", args.run_id]
        )
        _run_module(
            log,
            "manipulation_metrics",
            "abx.manipulation_metrics",
            ["--run-id", args.run_id],
        )
        _run_module(
            log,
            "manipulation_fronts_to_tasks",
            "abx.manipulation_fronts_to_tasks",
            ["--run-id", args.run_id],
        )
        _run_module(
            log, "task_roi_report", "abx.task_roi_report", ["--run-id", args.run_id]
        )
    else:
        log.append(
            {
                "ts": _utc_now_iso(),
                "step": "acquire_skipped",
                "skip_acquire": bool(args.skip_acquire),
                "n_tasks": n_tasks,
            }
        )

    _run_module(log, "evidence_metrics(post)", "abx.evidence_metrics", [])
    _run_module(log, "time_to_truth(post)", "abx.claim_timeseries", [])
    _run_module(log, "proof_integrity(post)", "abx.proof_integrity", [])
    _run_module(
        log, "aalmanac_enrich", "abx.aalmanac_enrich", ["--run-id", args.run_id]
    )
    _run_module(log, "aalmanac_tau", "abx.aalmanac_tau", ["--run-id", args.run_id])

    _run_module(log, "attribution_compile", "abx.attribution_compile", [])
    _run_module(log, "attribution_delta", "abx.attribution_delta", [])
    _run_module(log, "delta_scoring", "abx.delta_scoring", [])

    _write_json(cycle_log_path, {"meta": meta, "log": log})
    print(f"[CYCLE] wrote: {cycle_log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
