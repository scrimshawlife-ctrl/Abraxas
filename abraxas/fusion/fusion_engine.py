from __future__ import annotations

from collections import defaultdict

from abraxas.fusion.conflict_detector import detect_conflicts
from abraxas.fusion.models import CrossDomainSignal

POLARITY_WEIGHTS = {
    "positive": 1.0,
    "neutral": 0.5,
    "negative": -1.0,
    "unknown": 0.0,
}


def _base_report() -> dict[str, object]:
    return {
        "schema_version": "CrossDomainFusionReport.v1",
        "status": "NOT_COMPUTABLE",
        "authority": "CANDIDATE_ONLY",
        "dominant_domain": None,
        "domain_scores": {},
        "unknown_domains": [],
        "conflicts": [],
        "meta_confidence": 0.0,
        "provenance": {
            "deterministic": True,
            "inputs_count": 0,
            "computable_count": 0,
        },
    }


def fuse_signals(signals: list[dict]) -> dict[str, object]:
    report = _base_report()
    report["provenance"]["inputs_count"] = len(signals)
    computable: list[CrossDomainSignal] = []
    unknown_domains = set()

    for item in signals:
        try:
            signal = CrossDomainSignal.from_dict(item)
        except Exception:
            return report
        computable.append(signal)
        if signal.domain == "unknown":
            unknown_domains.add(signal.signal_id)

    if not computable:
        return report

    report["provenance"]["computable_count"] = len(computable)
    buckets: dict[str, list[float]] = defaultdict(list)
    confidences: list[float] = []
    for signal in computable:
        score = signal.magnitude * signal.confidence * signal.freshness * POLARITY_WEIGHTS[signal.polarity]
        buckets[signal.domain].append(score)
        confidences.append(signal.confidence)

    domain_scores = {domain: round(sum(values) / len(values), 6) for domain, values in sorted(buckets.items())}
    dominant_domain = max(domain_scores.items(), key=lambda kv: (abs(kv[1]), kv[0]))[0]

    report.update(
        {
            "status": "CANDIDATE_ONLY",
            "dominant_domain": dominant_domain,
            "domain_scores": domain_scores,
            "unknown_domains": sorted(unknown_domains),
            "conflicts": detect_conflicts(domain_scores),
            "meta_confidence": round(sum(confidences) / len(confidences), 6),
        }
    )
    return report
