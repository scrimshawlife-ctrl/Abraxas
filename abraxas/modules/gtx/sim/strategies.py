import random
from typing import Dict, List, Tuple

Action = int


def always_cooperate(_: List[Tuple[Action, Action]], __: Dict) -> Action:
    return 0


def always_defect(_: List[Tuple[Action, Action]], __: Dict) -> Action:
    return 1


def tit_for_tat(history: List[Tuple[Action, Action]], _: Dict) -> Action:
    if not history:
        return 0
    return history[-1][1]


def grim_trigger(history: List[Tuple[Action, Action]], _: Dict) -> Action:
    if any(opp == 1 for _, opp in history):
        return 1
    return 0


def win_stay_lose_shift(history: List[Tuple[Action, Action]], params: Dict) -> Action:
    threshold = float(params.get("threshold", 2.0))
    if not history:
        return 0
    last_self, last_opp = history[-1]
    win = last_opp == 0
    if win and threshold <= 2.0:
        return last_self
    if win and threshold > 2.0:
        return last_self
    return 1 - last_self


def random_p(_: List[Tuple[Action, Action]], params: Dict, rng: random.Random) -> Action:
    p = float(params.get("p_defect", 0.5))
    return 1 if rng.random() < p else 0
