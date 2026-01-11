from typing import Dict, List, Tuple

Action = int


def cooperation_rate(history: List[Tuple[Action, Action]]) -> Dict[str, float]:
    if not history:
        return {"p1": 0.0, "p2": 0.0}
    p1c = sum(1 for a1, _ in history if a1 == 0) / len(history)
    p2c = sum(1 for _, a2 in history if a2 == 0) / len(history)
    return {"p1": p1c, "p2": p2c}


def defection_streaks(history: List[Tuple[Action, Action]]) -> Dict[str, int]:
    def max_streak(seq: List[int]) -> int:
        best = 0
        current = 0
        for x in seq:
            if x == 1:
                current += 1
                best = max(best, current)
            else:
                current = 0
        return best

    return {
        "p1_max": max_streak([a1 for a1, _ in history]),
        "p2_max": max_streak([a2 for _, a2 in history]),
    }


def gini(values: List[float]) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    n = len(sorted_vals)
    cumulative = 0.0
    for idx, val in enumerate(sorted_vals, start=1):
        cumulative += idx * val
    return (2 * cumulative) / (n * total) - (n + 1) / n
