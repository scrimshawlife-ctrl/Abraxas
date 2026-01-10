from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

GameName = Literal[
    "prisoners_dilemma",
    "stag_hunt",
    "chicken",
    "battle_of_sexes",
    "matching_pennies",
    "public_goods",
]

StrategyName = Literal[
    "always_cooperate",
    "always_defect",
    "tit_for_tat",
    "grim_trigger",
    "random_p",
    "win_stay_lose_shift",
]


@dataclass(frozen=True)
class GTIRv01:
    """
    GT-IR v0.1 — Game Theory Input Representation
    Deterministic: no hidden randomness; any randomness must be seed-explicit.
    """

    version: str
    game: GameName
    rounds: int
    players: int
    seed: int
    payoff_matrix: Optional[Dict[str, List[List[float]]]] = None
    strategies: Optional[List[StrategyName]] = None
    strategy_params: Optional[Dict[str, Dict[str, float]]] = None
    notes: Optional[str] = None
