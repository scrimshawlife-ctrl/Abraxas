from __future__ import annotations

import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from abraxas.evolve.ledger import append_chained_jsonl


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_dt(s: str) -> datetime:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


HORIZON_DAYS = {
    "days": 3,
    "weeks": 21,
    "months": 120,
    "years_1": 420,
    "years_5": 2100,
}


def _pred_id(term: str, ts_issued: str, horizon: str) -> str:
    raw = f"{term.strip().lower()}|{ts_issued}|{horizon}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def issue_prediction(
    *,
    term: str,
    p: float,
    horizon: str,
    run_id: str,
    expected_error_band: Optional[Dict[str, Any]] = None,
    phase_context: Optional[Dict[str, Any]] = None,
    evidence: Optional[List[Dict[str, Any]]] = None,
    ts_issued: Optional[str] = None,
    ledger_path: str = "out/forecast_ledger/predictions.jsonl",
) -> Dict[str, Any]:
    ts = ts_issued or _utc_now_iso()
    h_days = int(HORIZON_DAYS.get(horizon, 21))
    start = _parse_dt(ts)
    end = (start + timedelta(days=h_days)).replace(microsecond=0).isoformat()
    pred_id = _pred_id(term, ts, horizon)

    row = {
        "version": "forecast_pred_row.v0.1",
        "pred_id": pred_id,
        "ts_issued": ts,
        "horizon": horizon,
        "window_start_ts": ts,
        "window_end_ts": end,
        "term": term,
        "p": max(0.0, min(1.0, float(p))),
        "phase_context": phase_context or {},
        "expected_error_band": expected_error_band or {},
        "evidence": evidence or [],
        "provenance": {"run_id": run_id, "method": "issue_prediction.v0.1"},
    }
    append_chained_jsonl(ledger_path, row)
    return row


def record_outcome(
    *,
    pred_id: str,
    result: str,
    run_id: str,
    evidence: Optional[List[Dict[str, Any]]] = None,
    notes: str = "",
    ts_observed: Optional[str] = None,
    ledger_path: str = "out/forecast_ledger/outcomes.jsonl",
) -> Dict[str, Any]:
    ts = ts_observed or _utc_now_iso()
    row = {
        "version": "forecast_outcome_row.v0.1",
        "pred_id": pred_id,
        "ts_observed": ts,
        "result": result,
        "notes": notes,
        "evidence": evidence or [],
        "provenance": {"run_id": run_id, "method": "record_outcome.v0.1"},
    }
    append_chained_jsonl(ledger_path, row)
    return row
