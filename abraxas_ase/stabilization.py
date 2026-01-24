from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class StabilizationParams:
    min_cycles_before_core: int = 7
    min_cycles_before_seal: int = 14


def update_cycles(
    *,
    prev_cycles_alive: int,
    prev_cycles_stable: int,
    prev_lane: str,
    new_lane: str,
) -> Tuple[int, int]:
    cycles_alive = int(prev_cycles_alive) + 1
    if prev_lane == new_lane:
        cycles_stable = int(prev_cycles_stable) + 1
    else:
        cycles_stable = 1
    return cycles_alive, cycles_stable


def allow_core_promotion(cycles_alive: int, params: StabilizationParams) -> bool:
    return int(cycles_alive) >= int(params.min_cycles_before_core)


def can_seal_core(cycles_alive: int, cycles_stable: int, params: StabilizationParams) -> bool:
    return int(cycles_alive) >= int(params.min_cycles_before_core) and int(cycles_stable) >= int(params.min_cycles_before_seal)


def apply_stabilization(
    *,
    lane_final: str,
    prev_lane: str,
    prev_cycles_alive: int,
    prev_cycles_stable: int,
    params: StabilizationParams,
) -> Tuple[str, int, int, bool]:
    blocked = False
    if lane_final == "core" and prev_lane != "core":
        if not allow_core_promotion(prev_cycles_alive + 1, params):
            lane_final = prev_lane
            blocked = True
    cycles_alive, cycles_stable = update_cycles(
        prev_cycles_alive=prev_cycles_alive,
        prev_cycles_stable=prev_cycles_stable,
        prev_lane=prev_lane,
        new_lane=lane_final,
    )
    return lane_final, cycles_alive, cycles_stable, blocked
