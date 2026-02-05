from __future__ import annotations

from io import BytesIO

from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse

from ..compare import compare_runs
from ..export_bundle import build_bundle
from ..policy import policy_snapshot
from .. import panel_context


def ui_export_bundle(request: Request):
    left_id = request.query_params.get("left")
    right_id = request.query_params.get("right")
    if not left_id or not right_id:
        raise HTTPException(status_code=404, detail="left and right run_id required")

    left = panel_context.store.get(left_id)
    right = panel_context.store.get(right_id)
    if not left or not right:
        raise HTTPException(status_code=404, detail="run not found")

    compare_summary = compare_runs(left, right)
    snapshot = policy_snapshot()
    bundle_bytes = build_bundle(
        left_run=left,
        right_run=right,
        compare_summary=compare_summary,
        policy_snapshot=snapshot,
        ledger_store=panel_context.ledger,
    )
    filename = f"abx_bundle_{left_id}_{right_id}.zip"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(BytesIO(bundle_bytes), media_type="application/zip", headers=headers)


def register(app):
    app.get("/export/bundle")(ui_export_bundle)
