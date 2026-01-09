from __future__ import annotations
from typing import Any, Dict, List

from abx.bus.runtime import process
from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_string
# render_output replaced by core.rendering.render_output capability
# analyze_text_for_drift replaced by drift.orchestrator.analyze_text_for_drift capability
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext

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

    # Create context for capability invocations
    ctx = RuneInvocationContext(
        run_id=frame_id,
        subsystem_id="abx.ui.chat_engine",
        git_hash="unknown"
    )

    # Render output via capability contract
    render_result = invoke_capability(
        "core.rendering.render_output",
        {"draft_text": draft_text, "context": context},
        ctx=ctx,
        strict_execution=True
    )
    rendered_text = render_result["rendered_text"]

    # Build provenance bundle
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

    # Analyze drift via capability contract
    drift_result = invoke_capability(
        "drift.orchestrator.analyze_text_for_drift",
        {"text": rendered_text, "provenance": provenance.model_dump()},
        ctx=ctx,
        strict_execution=True
    )
    drift_report_dict = drift_result["drift_report"]

    assistant = {
        "role": "assistant",
        "content": rendered_text,
        "meta": {
            "frame_id": frame_id,
            "modules": selected_modules or [],
            "drift_report": drift_report_dict,
        },
    }
    return {"assistant": assistant, "frame": frame}
