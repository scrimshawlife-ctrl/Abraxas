import random
from typing import Callable, Dict, List, Tuple

from .strategies import (
    always_cooperate,
    always_defect,
    grim_trigger,
    random_p,
    tit_for_tat,
    win_stay_lose_shift,
)

Action = int
History = List[Tuple[Action, Action]]

STRATEGY_TABLE: Dict[str, Callable] = {
    "always_cooperate": always_cooperate,
    "always_defect": always_defect,
    "tit_for_tat": tit_for_tat,
    "grim_trigger": grim_trigger,
    "win_stay_lose_shift": win_stay_lose_shift,
    "random_p": random_p,
}


def _payoff(payoff_matrix: Dict[str, List[List[float]]], a1: Action, a2: Action) -> Tuple[float, float]:
    p1 = payoff_matrix["P1"][a1][a2]
    p2 = payoff_matrix["P2"][a1][a2]
    return p1, p2


def run_2p_matrix_game(
    payoff_matrix: Dict[str, List[List[float]]],
    strat1: str,
    strat2: str,
    rounds: int,
    seed: int,
    params1: Dict,
    params2: Dict,
) -> Dict:
    rng = random.Random(seed)
    history: History = []
    p1_total = 0.0
    p2_total = 0.0

    for _ in range(rounds):
        s1 = STRATEGY_TABLE[strat1]
        s2 = STRATEGY_TABLE[strat2]

        a1 = s1(history, params1, rng) if strat1 == "random_p" else s1(history, params1)
        flipped = [(b, a) for (a, b) in history]
        a2 = s2(flipped, params2, rng) if strat2 == "random_p" else s2(flipped, params2)

        p1, p2 = _payoff(payoff_matrix, a1, a2)
        p1_total += p1
        p2_total += p2
        history.append((a1, a2))

    return {
        "rounds": rounds,
        "seed": seed,
        "strategy_p1": strat1,
        "strategy_p2": strat2,
        "p1_total": p1_total,
        "p2_total": p2_total,
        "p1_avg": p1_total / rounds,
        "p2_avg": p2_total / rounds,
        "history": history,
    }
