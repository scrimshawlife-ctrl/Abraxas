from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence


def compute_decay_v0(age_hours: float) -> float:
    if age_hours <= 0:
        return 1.0
    decay = 1.0 / (1.0 + age_hours / 24.0)
    return round(max(0.1, min(1.0, decay)), 6)


def bound_evidence_v0(evidence: Sequence[str], *, limit: int = 5) -> list[str]:
    cleaned = sorted({str(x).strip() for x in evidence if str(x).strip()})
    return cleaned[:limit]


def compress_signal_v0(observations: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in observations:
        grouped[(str(row.get("domain", "unknown")), str(row.get("subdomain", "unknown")))].append(row)

    out: list[dict[str, Any]] = []
    for (domain, subdomain), rows in sorted(grouped.items(), key=lambda x: x[0]):
        n = float(len(rows))
        score = sum(float(r.get("score", 0.0)) for r in rows) / n
        confidence = sum(float(r.get("confidence", 0.0)) for r in rows) / n
        max_age = max(float(r.get("age_hours", 0.0)) for r in rows)
        evidence = [e for r in rows for e in (r.get("evidence_refs") or [])]
        out.append(
            {
                "domain": domain,
                "subdomain": subdomain,
                "score": round(score, 6),
                "confidence": round(confidence, 6),
                "decay": compute_decay_v0(max_age),
                "evidence_refs": bound_evidence_v0(evidence, limit=5),
            }
        )
    return out


def dedupe_signal_items_v0(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for item in items:
        key = (str(item["domain"]), str(item["subdomain"]))
        if key not in seen:
            seen[key] = dict(item)
            continue
        if float(item.get("score", 0.0)) > float(seen[key].get("score", 0.0)):
            seen[key] = dict(item)
    return [seen[k] for k in sorted(seen.keys())]
