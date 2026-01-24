from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

LANE_ORDER = {
    "candidate": 0,
    "shadow": 1,
    "canary": 2,
    "core": 3,
}


@dataclass(frozen=True)
class HysteresisParams:
    promote_days_required: Dict[str, int] = field(default_factory=lambda: {
        "shadow": 2,
        "canary": 3,
        "core": 5,
    })
    demote_days_required: Dict[str, int] = field(default_factory=lambda: {
        "canary": 3,
        "shadow": 4,
    })


@dataclass(frozen=True)
class HysteresisState:
    above_counts: Dict[str, int]
    below_counts: Dict[str, int]
    last_lane: str


def default_state() -> HysteresisState:
    return HysteresisState(
        above_counts={"shadow": 0, "canary": 0, "core": 0},
        below_counts={"canary": 0, "shadow": 0},
        last_lane="candidate",
    )


def state_from_dict(data: Dict[str, object] | None) -> HysteresisState:
    if not data:
        return default_state()
    above = data.get("above_counts", {}) if isinstance(data, dict) else {}
    below = data.get("below_counts", {}) if isinstance(data, dict) else {}
    last_lane = data.get("last_lane", "candidate") if isinstance(data, dict) else "candidate"
    return HysteresisState(
        above_counts={
            "shadow": int(above.get("shadow", 0)),
            "canary": int(above.get("canary", 0)),
            "core": int(above.get("core", 0)),
        },
        below_counts={
            "canary": int(below.get("canary", 0)),
            "shadow": int(below.get("shadow", 0)),
        },
        last_lane=str(last_lane),
    )


def state_to_dict(state: HysteresisState) -> Dict[str, object]:
    return {
        "above_counts": dict(state.above_counts),
        "below_counts": dict(state.below_counts),
        "last_lane": state.last_lane,
    }


def apply_hysteresis(
    suggested_lane: str,
    prev_state: HysteresisState,
    params: HysteresisParams,
) -> Tuple[str, HysteresisState, Dict[str, object]]:
    suggested_lane = suggested_lane if suggested_lane in LANE_ORDER else "candidate"
    last_lane = prev_state.last_lane if prev_state.last_lane in LANE_ORDER else "candidate"
    suggested_rank = LANE_ORDER[suggested_lane]
    last_rank = LANE_ORDER[last_lane]

    above_counts = dict(prev_state.above_counts)
    below_counts = dict(prev_state.below_counts)

    for lane in ["shadow", "canary", "core"]:
        if suggested_rank >= LANE_ORDER[lane]:
            above_counts[lane] = int(above_counts.get(lane, 0)) + 1
        else:
            above_counts[lane] = 0

    if suggested_rank <= LANE_ORDER["canary"]:
        below_counts["canary"] = int(below_counts.get("canary", 0)) + 1
    else:
        below_counts["canary"] = 0

    if suggested_rank <= LANE_ORDER["shadow"]:
        below_counts["shadow"] = int(below_counts.get("shadow", 0)) + 1
    else:
        below_counts["shadow"] = 0

    final_lane = last_lane
    promoted = False
    demoted = False
    reason = "hold"

    if suggested_rank > last_rank:
        required = int(params.promote_days_required.get(suggested_lane, 1))
        if above_counts.get(suggested_lane, 0) >= required:
            final_lane = suggested_lane
            promoted = True
            reason = "promote"
        else:
            reason = "promote_wait"
    elif suggested_rank < last_rank:
        if last_lane == "core":
            required = int(params.demote_days_required.get("canary", 1))
            if below_counts.get("canary", 0) >= required:
                final_lane = suggested_lane
                demoted = True
                reason = "demote_core"
            else:
                reason = "demote_wait"
        elif last_lane in {"canary", "shadow"}:
            required = int(params.demote_days_required.get("shadow", 1))
            if below_counts.get("shadow", 0) >= required:
                final_lane = suggested_lane
                demoted = True
                reason = "demote"
            else:
                reason = "demote_wait"
        else:
            reason = "demote_hold"

    new_state = HysteresisState(
        above_counts=above_counts,
        below_counts=below_counts,
        last_lane=final_lane,
    )
    info = {
        "suggested_lane": suggested_lane,
        "final_lane": final_lane,
        "promoted": promoted,
        "demoted": demoted,
        "reason": reason,
    }
    return final_lane, new_state, info
