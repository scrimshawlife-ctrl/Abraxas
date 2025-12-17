from __future__ import annotations
from typing import Any, Dict, List

from abx.bus.runtime import process

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

    assistant = {
        "role": "assistant",
        "content": f"[stub] Processed: {last_user[:200]}",
        "meta": {"frame_id": frame.get("meta", {}).get("frame_id"), "modules": selected_modules or []},
    }
    return {"assistant": assistant, "frame": frame}
