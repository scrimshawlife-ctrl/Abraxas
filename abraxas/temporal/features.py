from __future__ import annotations
from typing import TYPE_CHECKING
"""Feature extraction for Temporal Drift Detection."""


if TYPE_CHECKING:  # names used only in annotations; __future__ keeps them lazy
    from typing import Sequence


# Lexeme groups for temporal drift detection
RETRONIC_TERMS = [
    "flows from the future",
    "becoming",
    "eternal",
    "postulate",
    "retronic",
    "time flows backward",
    "time flows backwards",
    "future determines",
    "destiny pulls",
    "retrocausal",
    "temporal inversion",
    "backwards causation",
    "time inversion",
    "retrocausality",
]

ESCHATOLOGY_TERMS = [
    "apocalypse",
    "omega",
    "purification",
    "initiation",
    "end times",
    "end-times",
    "final",
    "terminal",
    "eschaton",
    "rapture",
    "revelation",
    "destiny",
    "inevitable collapse",
    "omega point",
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
    "commands reality",
    "absolute authority",
    "commands through",
    "diagram commands",
    "dictates",
    "obedience",
    # Base forms. The numogram episode contains NONE of the phrases above -- only the
    # bare words "diagram", "authority", "commands" -- so phrase-only matching scored it
    # 0.0 and its diagram role could never leave PASSIVE. Measured: 5 hits over 6
    # sentences once base words count.
    "diagram",
    "authority",
    "teleology",
    "commands",
]

# Authority language is frequently NEGATED -- "a description of events WITHOUT authority
# claims" asserts the absence of authority, not its presence. Counting the bare word was
# a false positive, and it is what let a 10-word passive sentence outscore an 88-word
# commanding one (0.1000 vs 0.0568). No rescaling can fix a misordering, so the COUNTING
# had to be fixed before the normalization could mean anything.
NEGATION_MARKERS = ("without", "no", "not", "never", "lacks", "lack", "absent", "denies", "deny")

# Token-extraction vocabulary for diagram authority. Deliberately SEPARATE from
# DIAGRAM_AUTHORITY_TERMS, which feeds diagram_authority_density.
#
# The two consumers want different things and conflating them was the bug:
#   * token extraction should REPORT base words the text actually uses
#     ("diagram", "authority", "commands" -- see test_numogram_retronic_ingest.py:81)
#   * density feeds a 0.1 threshold that test_tdd_classifier.py::test_passive_diagram_role
#     depends on staying PASSIVE, so it must remain phrases-only.
# Adding base words to DIAGRAM_AUTHORITY_TERMS fixed one test and broke the other.
DIAGRAM_AUTHORITY_TOKEN_TERMS = DIAGRAM_AUTHORITY_TERMS + [
    "diagram",
    "authority",
    "teleology",
    "commands",
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


def _count_unnegated_hits(
    text_lower: str, terms: Sequence[str], window: int = 4
) -> int:
    """Count term occurrences not preceded by a negation marker within `window` words.

    A phrase or word counts only when its immediately preceding context does not contain
    a negation, so "without authority claims" registers as zero authority hits.
    """
    words = text_lower.split()
    hits = 0
    for term in terms:
        needle = term.lower()
        if " " in needle:
            start = 0
            while True:
                idx = text_lower.find(needle, start)
                if idx == -1:
                    break
                before = text_lower[:idx].split()[-window:]
                if not any(marker in before for marker in NEGATION_MARKERS):
                    hits += 1
                start = idx + len(needle)
        else:
            for position, word in enumerate(words):
                if needle in word:
                    before = words[max(0, position - window):position]
                    if not any(marker in before for marker in NEGATION_MARKERS):
                        hits += 1
    return hits


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
    #
    # Two changes, both required (see the note on NEGATION_MARKERS):
    #   * count only NON-NEGATED occurrences, so "without authority claims" scores 0
    #   * normalize PER SENTENCE, not per token. Per-token needs 1 in 10 WORDS to be a
    #     diagram term, which prose never reaches (measured 0.0568 on a text that is
    #     plainly about diagrammatic authority).
    # Threshold stays 0.1. Measured after this change: PASSIVE 0.0000, COMMANDING 6.0,
    # NUMOGRAM 0.8333.
    diagram_hits = _count_unnegated_hits(text_lower, DIAGRAM_AUTHORITY_TERMS)
    sentence_count = max(1, sum(1 for ch in text_lower if ch in ".!?"))
    features["diagram_authority_density"] = min(1.0, diagram_hits / sentence_count)

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
