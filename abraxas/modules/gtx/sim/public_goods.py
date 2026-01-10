from typing import Dict, List


def run_public_goods(
    contributions: List[float],
    multiplier: float = 1.6,
    seed: int | None = None,
) -> Dict[str, float]:
    total = sum(contributions)
    pool = total * multiplier
    share = pool / len(contributions) if contributions else 0.0
    payoffs = [share - c for c in contributions]
    return {
        "total": total,
        "pool": pool,
        "share": share,
        "payoffs": payoffs,
    }
