"""
Scenario Envelope Generator

Produces deterministic envelope configurations by modulating simulation priors.
No randomness; all envelope variants are pre-specified.
"""

from __future__ import annotations

from typing import Dict, List


def build_envelopes(base_priors: Dict[str, float]) -> List[Dict[str, any]]:
    """
    Generate deterministic scenario envelopes from base priors.

    Creates 4 standard envelopes:
    1. baseline: as-is priors
    2. push_spread_up: MRI +0.15 (clipped to [0,1])
    3. damping_up: IRI +0.15 (clipped to [0,1])
    4. memory_long: tau_memory +0.20, tau_latency +0.10 (clipped)

    Args:
        base_priors: Dictionary of base simulation knobs

    Returns:
        List of envelope dictionaries with label, priors, and falsifiers
    """

    def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clamp value to [min_val, max_val]."""
        return max(min_val, min(max_val, value))

    # Extract base values with defaults
    mri_base = base_priors.get("MRI", 0.5)
    iri_base = base_priors.get("IRI", 0.5)
    tau_memory_base = base_priors.get("tau_memory", 0.5)
    tau_latency_base = base_priors.get("tau_latency", 0.3)

    envelopes = []

    # Envelope 1: Baseline (no modulation)
    envelopes.append({
        "label": "baseline",
        "priors": base_priors.copy(),
        "falsifiers": [
            "Observed spread diverges significantly from baseline MRI",
            "Damping dynamics violate baseline IRI assumptions",
        ]
    })

    # Envelope 2: Push Spread Up (MRI +0.15)
    mri_high = clamp(mri_base + 0.15)
    envelopes.append({
        "label": "push_spread_up",
        "priors": {
            **base_priors,
            "MRI": mri_high
        },
        "falsifiers": [
            "Phrase rigidity (MDS) increases while spread stays flat",
            "Cross-cluster correlations decrease despite high MRI",
        ]
    })

    # Envelope 3: Damping Up (IRI +0.15)
    iri_high = clamp(iri_base + 0.15)
    envelopes.append({
        "label": "damping_up",
        "priors": {
            **base_priors,
            "IRI": iri_high
        },
        "falsifiers": [
            "Intervention response time lengthens despite high IRI",
            "Counter-narrative effectiveness shows no improvement",
        ]
    })

    # Envelope 4: Memory Long (tau_memory +0.20, tau_latency +0.10)
    tau_memory_long = clamp(tau_memory_base + 0.20)
    tau_latency_long = clamp(tau_latency_base + 0.10)
    envelopes.append({
        "label": "memory_long",
        "priors": {
            **base_priors,
            "tau_memory": tau_memory_long,
            "tau_latency": tau_latency_long,
        },
        "falsifiers": [
            "Narrative persistence decays faster than tau_memory predicts",
            "Latency effects disappear earlier than tau_latency window",
        ]
    })

    return envelopes
