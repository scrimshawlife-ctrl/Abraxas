"""Feature extraction for Temporal Drift Detection."""

from __future__ import annotations


# Lexeme groups for temporal drift detection
RETRONIC_TERMS = [
    "flows from the future",
    "becoming",
    "eternal",
    "postulate",
    "retronic",
    "time flows backward",
    "future determines",
    "destiny pulls",
]

ESCHATOLOGY_TERMS = [
    "apocalypse",
    "omega",
    "purification",
    "initiation",
    "end times",
    "final",
    "terminal",
    "eschaton",
    "rapture",
    "revelation",
]

DIAGRAM_AUTHORITY_TERMS = [
    "time spiral",
    "zones",
    "gates",
    "psychic organs",
    "numogram",
    "diagram shows",
    "map reveals",
    "chart proves",
    "glyph",
    "sigil",
]

AGENCY_TERMS = [
    "time wants",
    "numbers act",
    "forces seek",
    "destiny demands",
    "pattern requires",
    "system drives",
    "process compels",
    "inevitable",
]


def extract_temporal_features(text: str) -> dict[str, float]:
    """
    Extract temporal drift features from text.

    Returns normalized feature dict with values in [0, 1] range.
    """
    text_lower = text.lower()
    tokens = text.split()
    token_count = max(len(tokens), 1)  # Avoid division by zero

    features = {}

    # Retronic/inverted time density
    retronic_hits = sum(
        text_lower.count(term.lower()) for term in RETRONIC_TERMS
    )
    features["retronic_density"] = min(1.0, retronic_hits / token_count)

    # Eschatological language density
    eschatology_hits = sum(
        text_lower.count(term.lower()) for term in ESCHATOLOGY_TERMS
    )
    features["eschatology_density"] = min(1.0, eschatology_hits / token_count)

    # Diagram authority density
    diagram_hits = sum(
        text_lower.count(term.lower()) for term in DIAGRAM_AUTHORITY_TERMS
    )
    features["diagram_authority_density"] = min(1.0, diagram_hits / token_count)

    # Agency migration density (non-human agents)
    agency_hits = sum(text_lower.count(term.lower()) for term in AGENCY_TERMS)
    features["agency_migration_density"] = min(1.0, agency_hits / token_count)

    # Causality assertion markers
    causality_markers = [
        "therefore",
        "because",
        "causes",
        "must",
        "inevitably",
        "necessarily",
    ]
    causality_hits = sum(
        text_lower.count(marker) for marker in causality_markers
    )
    features["causality_assertion"] = min(1.0, causality_hits / token_count)

    # Future-tense determinism
    future_determinism = ["will be", "shall", "destined", "fated", "predetermined"]
    future_hits = sum(text_lower.count(term) for term in future_determinism)
    features["future_determinism"] = min(1.0, future_hits / token_count)

    return features


def compute_temporal_signature(features: dict[str, float]) -> dict[str, float]:
    """
    Compute aggregate temporal signature from features.

    Returns weighted scores for major categories.
    """
    signature = {}

    # Retronic/inverted score
    signature["retronic_score"] = (
        features.get("retronic_density", 0.0) * 2.0
        + features.get("future_determinism", 0.0)
    ) / 3.0

    # Eschatological score
    signature["eschatological_score"] = (
        features.get("eschatology_density", 0.0) * 2.0
        + features.get("future_determinism", 0.0)
    ) / 3.0

    # Diagram authority score
    signature["diagram_authority_score"] = features.get("diagram_authority_density", 0.0)

    # Sovereignty risk score (agency migration + causality assertion)
    signature["sovereignty_risk_score"] = (
        features.get("agency_migration_density", 0.0)
        + features.get("causality_assertion", 0.0)
    ) / 2.0

    # Normalize all to [0, 1]
    for key in signature:
        signature[key] = min(1.0, signature[key])

    return signature
