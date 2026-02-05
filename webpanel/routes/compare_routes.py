from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from ..compare import compare_runs
from ..panel_context import _panel_host, _panel_port, _panel_token, _token_enabled, templates
from ..policy import compute_policy_hash, get_policy_snapshot
from .. import panel_context


def ui_compare(request: Request):
    left_id = request.query_params.get("left")
    right_id = request.query_params.get("right")
    if not left_id or not right_id:
        raise HTTPException(status_code=404, detail="left and right run_id required")

    left = panel_context.store.get(left_id)
    right = panel_context.store.get(right_id)
    if not left or not right:
        raise HTTPException(status_code=404, detail="run not found")

    compare_summary = compare_runs(left, right)
    current_snapshot = get_policy_snapshot()
    current_hash = compute_policy_hash(current_snapshot)
    left_ingest = left.policy_hash_at_ingest
    right_ingest = right.policy_hash_at_ingest
    left_match = left_ingest == current_hash if left_ingest else None
    right_match = right_ingest == current_hash if right_ingest else None
    ingest_diff = bool(left_ingest and right_ingest and left_ingest != right_ingest)

    return templates.TemplateResponse(
        "compare.html",
        {
            "request": request,
            "left": left,
            "right": right,
            "compare": compare_summary,
            "current_policy_hash": current_hash,
            "left_ingest_policy_hash": left_ingest,
            "right_ingest_policy_hash": right_ingest,
            "left_policy_match": left_match,
            "right_policy_match": right_match,
            "ingest_policy_diff": ingest_diff,
            "panel_host": _panel_host(),
            "panel_port": _panel_port(),
            "token_enabled": _token_enabled(),
            "panel_token": _panel_token(),
        },
    )


def register(app):
    app.get("/compare", response_class=HTMLResponse)(ui_compare)
