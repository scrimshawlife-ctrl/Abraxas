"""VBM corpus loading and normalization."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from abraxas.casebooks.vbm.models import VBMEpisode, VBMCasebook, VBMPhase
from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_canonical_json


# Trigger lexicon organized by phase
TRIGGER_LEXICON = {
    VBMPhase.UNFALSIFIABLE_CLOSURE: [
        "everything explains",
        "must coexist",
        "cannot revert",
        "single flow of time",
        "complete",
        "fundamental",
        "absolute",
        "universal truth",
    ],
    VBMPhase.CONSCIOUSNESS_ATTRIBUTION: [
        "consciousness",
        "apex of consciousness",
        "awareness",
        "sentience",
        "cosmic mind",
    ],
    VBMPhase.PHYSICS_LEXICON_INJECTION: [
        "tachyon",
        "monopole",
        "graviton",
        "ether",
        "zero-point",
        "inertia ether",
        "magnetic field",
        "photon",
        "electron",
        "particle",
    ],
    VBMPhase.CROSS_DOMAIN_ANALOGY: [
        "dna",
        "music",
        "binary",
        "nuclear",
        "biology",
        "galaxies",
        "aura",
        "chakra",
        "frequency",
        "vibration",
    ],
    VBMPhase.REPRESENTATION_REDUCTION: [
        "digital root",
        "reduces",
        "single digits",
        "returns to nine",
        "repeating decimals",
        "modular",
        "remainder",
    ],
    VBMPhase.MATH_PATTERN: [
        "pattern",
        "symmetry",
        "torus",
        "vortex",
        "doubling",
        "sequence",
        "arithmetic",
    ],
}


def load_episodes_from_fixtures(fixtures_dir: str | Path = "tests/fixtures/vbm") -> list[VBMEpisode]:
    """
    Load VBM episodes from fixture directory.

    Returns episodes in deterministic order (sorted by episode_id).
    """
    fixtures_path = Path(fixtures_dir)

    if not fixtures_path.exists():
        return []

    episodes = []

    # Load all episode_*.json files
    episode_files = sorted(fixtures_path.glob("episode_*.json"))

    for episode_file in episode_files:
        with open(episode_file, "r") as f:
            data = json.load(f)

        # Extract and normalize
        episode = _normalize_episode(data)
        episodes.append(episode)

    # Sort by episode_id for determinism
    episodes.sort(key=lambda e: e.episode_id)

    return episodes


def _normalize_episode(data: dict[str, Any]) -> VBMEpisode:
    """Normalize episode data from fixture."""
    episode_id = data["episode_id"]
    title = data["title"]
    summary_text = data["summary_text"]

    # Normalize whitespace
    summary_text = " ".join(summary_text.split())

    # Extract claims deterministically (first N sentences)
    extracted_claims = _extract_claims(summary_text)

    # Extract tokens deterministically
    extracted_tokens = _extract_tokens(summary_text)

    # Build provenance
    provenance = ProvenanceBundle(
        inputs=[
            ProvenanceRef(
                scheme="fixture",
                path=f"vbm/{episode_id}",
                sha256=hash_canonical_json(data),
            )
        ],
        transforms=["normalize_whitespace", "extract_claims", "extract_tokens"],
        metrics={"token_count": float(len(extracted_tokens))},
        created_by="vbm_corpus_loader",
    )

    return VBMEpisode(
        episode_id=episode_id,
        title=title,
        summary_text=summary_text,
        extracted_claims=extracted_claims,
        extracted_tokens=extracted_tokens,
        provenance=provenance,
    )


def _extract_claims(summary_text: str, max_claims: int = 5) -> list[str]:
    """
    Extract claims deterministically from summary text.

    Uses sentence splitting and takes first N sentences.
    """
    # Simple sentence split
    sentences = re.split(r'[.!?]+\s+', summary_text)

    # Clean and filter
    claims = []
    for sent in sentences[:max_claims]:
        sent = sent.strip()
        if len(sent) > 10:  # Minimum length
            claims.append(sent)

    return claims


def _extract_tokens(text: str) -> dict[str, int]:
    """
    Extract and count trigger lexemes from text.

    Returns deterministic counts using lowercased substring matching.
    """
    text_lower = text.lower()
    token_counts: dict[str, int] = {}

    # Check all lexemes from all phases
    for phase, lexemes in TRIGGER_LEXICON.items():
        for lexeme in lexemes:
            # Count occurrences with word boundary consideration
            # Simple approach: count lowercased substring occurrences
            count = text_lower.count(lexeme.lower())
            if count > 0:
                token_counts[lexeme] = count

    return token_counts


def build_casebook(episodes: list[VBMEpisode], phase_curve: list[dict[str, Any]] | None = None) -> VBMCasebook:
    """
    Build VBMCasebook from episodes.

    Args:
        episodes: List of episodes
        phase_curve: Optional pre-computed phase curve

    Returns:
        Complete VBMCasebook
    """
    # Build provenance
    provenance = ProvenanceBundle(
        inputs=[
            ProvenanceRef(
                scheme="episode",
                path=ep.episode_id,
                sha256=hash_canonical_json(ep.model_dump()),
            )
            for ep in episodes
        ],
        transforms=["aggregate_episodes"],
        metrics={"episode_count": float(len(episodes))},
        created_by="vbm_casebook_builder",
    )

    return VBMCasebook(
        casebook_id="VBM_SERIES",
        episodes=episodes,
        phase_curve=phase_curve or [],
        trigger_lexicon={phase.value: lexemes for phase, lexemes in TRIGGER_LEXICON.items()},
        provenance=provenance,
    )
