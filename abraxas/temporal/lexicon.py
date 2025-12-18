"""Temporal Firewall Lexicon - shared lexeme lists for drift detection and filtering."""

from __future__ import annotations

# Modal terms that assert inevitability, necessity, or absolute claims
MODAL_TERMS = [
    "must",
    "inevitable",
    "inevitably",
    "destined",
    "destiny",
    "cannot",
    "always",
    "never",
    "absolutely",
    "certainly",
    "necessarily",
    "required",
    "obligated",
    "compelled",
    "forced",
    "predetermined",
]

# Agency transfer patterns (agency migrates from subjects to abstractions)
AGENCY_TRANSFER = [
    "numbers act",
    "numbers want",
    "numbers determine",
    "time wants",
    "time requires",
    "time demands",
    "the diagram dictates",
    "the diagram commands",
    "the diagram determines",
    "the zone controls",
    "the zone dictates",
    "the zone determines",
    "the pattern decides",
    "the pattern commands",
    "the vortex controls",
    "the future determines",
    "the eschaton commands",
    "consciousness requires",
    "reality demands",
]

# Closure terms (eschatological, unfalsifiable, or totalizing language)
CLOSURE_TERMS = [
    "apocalypse",
    "apocalyptic",
    "omega",
    "omega point",
    "salvation",
    "purification",
    "initiation",
    "eschatology",
    "eschatological",
    "eschaton",
    "end-times",
    "final days",
    "ultimate truth",
    "absolute reality",
    "complete system",
    "total explanation",
    "everything is",
    "all is",
    "unified theory",
]

# Causality inversion patterns (retrocausal, backwards causation)
CAUSALITY_INVERSION = [
    "flows from the future",
    "future into the past",
    "future determines the past",
    "retronic",
    "retrocausal",
    "retrocausality",
    "backwards causation",
    "backwards in time",
    "reverse causality",
    "time flows backwards",
    "temporal inversion",
    "becoming into consciousness",
    "effect precedes cause",
    "caused by the future",
    "future causes past",
]

# Certainty patterns that should be softened in DE_ESCALATE mode
CERTAINTY_PATTERNS = [
    (r"\bis\b", "can be read as"),
    (r"\bmeans\b", "may suggest"),
    (r"\bproves\b", "indicates"),
    (r"\bshows that\b", "suggests that"),
    (r"\bdemonstrates that\b", "points toward"),
    (r"\breveals that\b", "hints that"),
    (r"\bclearly\b", "arguably"),
    (r"\bobviously\b", "potentially"),
]

# Metaphor markers for counting metaphorical density
METAPHOR_MARKERS = [
    "like",
    "as if",
    "resembles",
    "mirrors",
    "reflects",
    "embodies",
    "represents",
    "symbolizes",
    "parallels",
    "analogous to",
]


def count_lexeme_matches(text: str, lexemes: list[str]) -> int:
    """
    Count how many times any lexeme from the list appears in text (case-insensitive).

    Args:
        text: Text to search
        lexemes: List of lexemes to count

    Returns:
        Total count of all lexeme matches
    """
    text_lower = text.lower()
    count = 0
    for lexeme in lexemes:
        count += text_lower.count(lexeme.lower())
    return count


def extract_lexeme_matches(text: str, lexemes: list[str]) -> list[str]:
    """
    Extract all lexeme matches from text.

    Args:
        text: Text to search
        lexemes: List of lexemes to find

    Returns:
        List of lexemes that were found (deduplicated)
    """
    text_lower = text.lower()
    matches = []
    for lexeme in lexemes:
        if lexeme.lower() in text_lower:
            matches.append(lexeme)
    return sorted(list(set(matches)))
