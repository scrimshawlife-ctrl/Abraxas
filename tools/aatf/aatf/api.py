from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .export.bundle import export_bundle
from .queue.review import apply_review
from .queue.states import QueueState
from .storage import list_queue_items

app = FastAPI(title="AATF API", version="0.1.0")


class ReviewRequest(BaseModel):
    item_id: str
    decision: QueueState
    notes: str


class ExportRequest(BaseModel):
    types: list[str]
    out: str | None = None


@app.get("/queue")
def queue_list(state: str | None = None) -> dict:
    return {"items": list_queue_items(state=state)}


@app.post("/review")
def review_item(payload: ReviewRequest) -> dict:
    return apply_review(payload.item_id, payload.decision, payload.notes)


@app.post("/export")
def export_items(payload: ExportRequest) -> dict:
    return export_bundle(payload.types, out_path=payload.out)
