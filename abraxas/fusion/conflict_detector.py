from __future__ import annotations

from itertools import combinations


def detect_conflicts(domain_scores: dict[str, float]) -> list[dict[str, object]]:
    conflicts: list[dict[str, object]] = []
    items = sorted(domain_scores.items(), key=lambda item: item[0])
    for (domain_a, score_a), (domain_b, score_b) in combinations(items, 2):
        if score_a > 0 and score_b < 0 or score_a < 0 and score_b > 0:
            conflicts.append(
                {
                    "domain_a": domain_a,
                    "domain_b": domain_b,
                    "type": "POLARITY_CONFLICT",
                    "severity": round(min(abs(score_a), abs(score_b)), 6),
                }
            )
    return conflicts
