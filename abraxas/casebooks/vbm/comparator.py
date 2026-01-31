"""VBM comparator for scoring text against casebook."""

from __future__ import annotations

from abraxas.casebooks.vbm.features import extract_vbm_features, compute_escalation_score
from abraxas.casebooks.vbm.models import VBMDriftScore, VBMPhase
from abraxas.casebooks.vbm.phase import classify_phase, PHASE_WEIGHTS
from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_string


# Lattice operator mapping based on phase
PHASE_LATTICE_MAP = {
    VBMPhase.MATH_PATTERN: ["MKB"],  # Math Knowledge Base
    VBMPhase.REPRESENTATION_REDUCTION: ["MKB", "SCA"],  # + Symbolic Compression Analogy
    VBMPhase.CROSS_DOMAIN_ANALOGY: ["SCA", "DOE"],  # + Domain Overgeneralization
    VBMPhase.PHYSICS_LEXICON_INJECTION: ["DOE", "PAP"],  # + Physics Authority Pattern
    VBMPhase.CONSCIOUSNESS_ATTRIBUTION: ["PAM", "UCS"],  # Pattern Authority Metaphysics + Unfalsifiable Cosmic Scope
    VBMPhase.UNFALSIFIABLE_CLOSURE: ["UCS"],  # Unfalsifiable Cosmic Scope
}


def score_against_vbm(text: str, operator_hits: list[str] | None = None) -> VBMDriftScore:
    """
    Score text against VBM casebook.

    Args:
        text: Text to score
        operator_hits: Optional list of operator IDs already detected

    Returns:
        VBMDriftScore with phase, score, and lattice hits
    """
    if operator_hits is None:
        operator_hits = []

    # Extract features
    features = extract_vbm_features(text)

    # Classify phase
    phase, phase_confidence = classify_phase(text)

    # Compute escalation score
    score = compute_escalation_score(features)

    # Determine lattice hits
    lattice_hits = set(operator_hits)  # Start with provided hits

    # Add phase-based lattice hits
    phase_operators = PHASE_LATTICE_MAP.get(phase, [])
    lattice_hits.update(phase_operators)

    # Build evidence
    evidence = {
        "features": features,
        "phase_weight": PHASE_WEIGHTS.get(phase, 1.0),
        "token_hits": {k: v for k, v in features.items() if v > 0},
    }

    # Build provenance
    provenance = ProvenanceBundle(
        inputs=[
            ProvenanceRef(
                scheme="text",
                path="score_input",
                sha256=hash_string(text),
            )
        ],
        transforms=["extract_features", "classify_phase", "compute_score"],
        metrics={
            "score": score,
            "phase_confidence": phase_confidence,
            "feature_count": float(len(features)),
        },
        created_by="vbm_comparator",
    )

    return VBMDriftScore(
        score=score,
        phase=phase,
        phase_confidence=phase_confidence,
        lattice_hits=sorted(list(lattice_hits)),  # Sort for determinism
        evidence=evidence,
        provenance=provenance,
    )
