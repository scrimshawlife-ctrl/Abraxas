from __future__ import annotations

from typing import Callable, Dict

from abraxas.training.integrate_v1 import oracle_attach_training_shadow


OverlayHook = Callable[[Dict[str, object]], Dict[str, object]]

OVERLAY_HOOKS: Dict[str, OverlayHook] = {
    "training_shadow_v1": oracle_attach_training_shadow,
}


__all__ = ["OVERLAY_HOOKS", "OverlayHook"]
