from __future__ import annotations
from typing import Any, Dict, List, Optional

try:
    from fastapi import FastAPI
except Exception:
    FastAPI = None  # type: ignore

from abx.ui.admin_handshake import admin_prompt
from abx.ui.chat_engine import chat
from abx.store.sqlite_store import connect, init_db, latest_by_source

def build_ui_app() -> Any:
    if FastAPI is None:
        raise RuntimeError("FastAPI not installed; install fastapi+uvicorn or use minhttp fallback.")
    app = FastAPI(title="Abraxas UI", version="0.1.0-ui")

    @app.get("/admin/handshake")
    def handshake() -> Dict[str, Any]:
        return admin_prompt()

    @app.post("/chat")
    def chat_post(body: Dict[str, Any]) -> Dict[str, Any]:
        msgs = body.get("messages") or []
        selected = body.get("selected_modules") or []
        if not isinstance(msgs, list):
            msgs = []
        if not isinstance(selected, list):
            selected = []
        return chat(msgs, selected_modules=[str(x) for x in selected])

    @app.get("/data/latest")
    def data_latest(source: str, limit: int = 20) -> Dict[str, Any]:
        con = connect()
        init_db(con)
        rows = latest_by_source(con, source=source, limit=limit)
        return {"source": source, "items": rows}

    return app
