from __future__ import annotations

from abraxas_ase.stabilization import StabilizationParams, apply_stabilization


def test_stabilization_blocks_early_core() -> None:
    params = StabilizationParams(min_cycles_before_core=7, min_cycles_before_seal=14)
    lane, cycles_alive, cycles_stable, blocked = apply_stabilization(
        lane_final="core",
        prev_lane="canary",
        prev_cycles_alive=3,
        prev_cycles_stable=3,
        params=params,
    )

    assert blocked is True
    assert lane == "canary"
    assert cycles_alive == 4
