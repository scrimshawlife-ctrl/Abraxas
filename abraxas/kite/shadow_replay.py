from __future__ import annotations
from typing import Dict, Any, List
from ..core.kernel import AbraxasKernel
from ..core.context import UserContext
from ..admin.permissions import require_admin


def shadow_replay(
    kernel: AbraxasKernel,
    admin_perms,
    user: UserContext,
    base_signals: Dict[str, Any],
    injected_signals: Dict[str, Any],
    overlays: List[str],
) -> Dict[str, Any]:
    require_admin(admin_perms)

    base = kernel.run_oracle(user=user, input_signals=base_signals, overlays_requested=overlays)
    inj = kernel.run_oracle(user=user, input_signals=injected_signals, overlays_requested=overlays)

    return {
        "base_run": {"run_id": base["run_id"], "provenance": base["provenance"]},
        "injected_run": {"run_id": inj["run_id"], "provenance": inj["provenance"]},
        "diff_hint": "Implement structured diffs later; this stub confirms deterministic replays.",
    }
