from __future__ import annotations


def list_insight_views() -> list[str]:
    return [
        "run_overview",
        "proof_validation_closure",
        "boundary_trust",
        "incident_degradation",
        "causal_trace",
        "observability_health",
    ]
