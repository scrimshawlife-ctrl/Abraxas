from __future__ import annotations
from typing import Any, Dict, List

from abx.bus.runtime import process
from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_string
from abraxas.core.rendering import render_output
from abraxas.drift.orchestrator import analyze_text_for_drift

def chat(messages: List[Dict[str, Any]], *, selected_modules: List[str] | None = None) -> Dict[str, Any]:
    # messages: [{"role":"user"|"assistant"|"system","content":"..."}]
    # Deterministic stub: we run the bus pipeline using last user content as payload.
    last_user = ""
    for m in messages[::-1]:
        if m.get("role") == "user":
            last_user = str(m.get("content", ""))
            break

    payload = {"intent": "chat", "user_text": last_user, "messages": messages}
    # Optionally pass module selection hints
    if selected_modules:
        payload["selected_modules"] = selected_modules

    frame = process(payload)

    draft_text = str(frame.get("output", {}).get("message", ""))
    frame_id = str(frame.get("meta", {}).get("frame_id", "unknown_frame"))
    context = {"intent": payload.get("intent", "chat"), "frame_id": frame_id}
    rendered_text = render_output(draft_text, context=context)
    provenance = ProvenanceBundle(
        inputs=[
            ProvenanceRef(
                scheme="bus.frame",
                path=frame_id,
                sha256=hash_string(draft_text),
            )
        ],
        transforms=["abx.bus.process"],
        metadata={"context": context, "selected_modules": selected_modules or []},
    )
    drift_report = analyze_text_for_drift(rendered_text, provenance)

    assistant = {
        "role": "assistant",
        "content": rendered_text,
        "meta": {
            "frame_id": frame_id,
            "modules": selected_modules or [],
            "drift_report": drift_report.model_dump(),
        },
    }
    return {"assistant": assistant, "frame": frame}
