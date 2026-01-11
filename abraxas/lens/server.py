from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import json

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from abraxas.aalmanac.ars_store import (
    export_approved_proposals,
    latest_decision,
    list_candidates,
    open_store,
    set_decision,
    upsert_candidates_from_jsonl,
)


@dataclass(frozen=True)
class LensConfig:
    db_path: Path
    candidates_jsonl: Path
    proposals_out: Path
    bind_host: str = "127.0.0.1"
    bind_port: int = 8787


def create_app(cfg: LensConfig) -> FastAPI:
    app = FastAPI(title="LENS v0.1.0 (Local Evaluation & Notation Studio)")

    here = Path(__file__).resolve().parent
    templates = Jinja2Templates(directory=str(here / "templates"))

    static_dir = here / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    def _conn():
        return open_store(cfg.db_path)

    def _candidate_rows(limit: int = 50, min_score: float = 0.0):
        conn = _conn()
        try:
            rows = []
            for r in list_candidates(conn, limit=limit, min_score=min_score):
                dec = latest_decision(conn, r["id"])
                rows.append(
                    {
                        "id": r["id"],
                        "id_short": r["id"][:10] + "…",
                        "kind": r["kind"],
                        "term": r["term"],
                        "score": float(r["score"]),
                        "created_at_utc": int(r["created_at_utc"]),
                        "decision": (dec["decision"] if dec else None),
                        "decision_note": (dec["note"] if dec else ""),
                    }
                )
            return rows
        finally:
            conn.close()

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request, limit: int = 40, min_score: float = 0.5):
        rows = _candidate_rows(limit=limit, min_score=min_score)
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "cfg": cfg,
                "rows": rows,
                "limit": limit,
                "min_score": min_score,
            },
        )

    @app.get("/candidate/{candidate_id}", response_class=HTMLResponse)
    def candidate_detail(request: Request, candidate_id: str):
        conn = _conn()
        try:
            cur = conn.execute(
                "SELECT id, kind, term, score, payload_json, created_at_utc FROM ars_candidate WHERE id = ?",
                (candidate_id,),
            )
            row = cur.fetchone()
            if not row:
                return PlainTextResponse("Not found", status_code=404)

            payload = json.loads(row["payload_json"])
            dec = latest_decision(conn, candidate_id)
            return templates.TemplateResponse(
                "candidate.html",
                {
                    "request": request,
                    "row": dict(row),
                    "payload_pretty": json.dumps(
                        payload, indent=2, sort_keys=True, ensure_ascii=False
                    ),
                    "decision": (dict(dec) if dec else None),
                },
            )
        finally:
            conn.close()

    @app.post("/ingest")
    def ingest():
        conn = _conn()
        try:
            report = upsert_candidates_from_jsonl(conn, cfg.candidates_jsonl)
        finally:
            conn.close()
        return RedirectResponse(url=f"/?ingested={report['inserted']}", status_code=303)

    @app.post("/approve")
    def approve(
        candidate_id: str = Form(...),
        note: str = Form(""),
        reviewer: str = Form("admin"),
    ):
        conn = _conn()
        try:
            set_decision(conn, candidate_id, "approve", note=note, reviewer=reviewer)
        finally:
            conn.close()
        return RedirectResponse(url=f"/candidate/{candidate_id}", status_code=303)

    @app.post("/deny")
    def deny(
        candidate_id: str = Form(...),
        note: str = Form(""),
        reviewer: str = Form("admin"),
    ):
        conn = _conn()
        try:
            set_decision(conn, candidate_id, "deny", note=note, reviewer=reviewer)
        finally:
            conn.close()
        return RedirectResponse(url=f"/candidate/{candidate_id}", status_code=303)

    @app.post("/merge")
    def merge(
        candidate_id: str = Form(...),
        merge_into_id: str = Form(...),
        note: str = Form(""),
        reviewer: str = Form("admin"),
    ):
        conn = _conn()
        try:
            set_decision(
                conn,
                candidate_id,
                "merge",
                note=note,
                merge_into_id=merge_into_id,
                reviewer=reviewer,
            )
        finally:
            conn.close()
        return RedirectResponse(url=f"/candidate/{candidate_id}", status_code=303)

    @app.post("/export-approved")
    def export_approved():
        conn = _conn()
        try:
            export_approved_proposals(conn, cfg.proposals_out)
        finally:
            conn.close()
        return RedirectResponse(url="/?exported=1", status_code=303)

    @app.get("/healthz", response_class=PlainTextResponse)
    def healthz():
        return "ok"

    return app
