from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List
from abx.runtime.config import load_config
from abx.overlays.manager import OverlayManager
from abx.bus.runtime import build_registry
from abx.util.jsonutil import dumps_stable

@dataclass(frozen=True)
class CapabilitySnapshot:
    built_in_modules: List[str]
    overlays: List[str]

def discover() -> CapabilitySnapshot:
    cfg = load_config()
    reg = build_registry()
    mgr = OverlayManager(cfg.overlays_dir, cfg.state_dir)
    return CapabilitySnapshot(
        built_in_modules=reg.list(),
        overlays=mgr.list_overlays(),
    )

def admin_prompt() -> Dict[str, Any]:
    cap = discover()
    return {
        "type": "admin_handshake",
        "message": "Admin mode: modules detected. Choose interaction mode.",
        "modes": [
            {"id": "chat", "label": "Just interact with Abraxas (chat)"},
            {"id": "chat+modules", "label": "Chat + explicitly select modules/overlays"},
        ],
        "detected": {
            "built_in_modules": cap.built_in_modules,
            "overlays": cap.overlays,
        },
    }
