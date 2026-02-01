"""Numogram casebook corpus loading."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from abraxas.casebooks.numogram.models import NumogramEpisode, NumogramCasebook
from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_canonical_json
from abraxas.temporal.features import (
    RETRONIC_TERMS,
    ESCHATOLOGY_TERMS,
    DIAGRAM_AUTHORITY_TERMS,
    AGENCY_TERMS,
)


# Trigger lexicon for Numogram TT-CB
TRIGGER_LEXICON = {
    "retronic": RETRONIC_TERMS,
    "eschatology": ESCHATOLOGY_TERMS,
    "diagram_authority": DIAGRAM_AUTHORITY_TERMS,
    "agency": AGENCY_TERMS,
}


def load_numogram_episodes(fixtures_dir: str | Path = "tests/fixtures/numogram") -> list[NumogramEpisode]:
    """
    Load Numogram episodes from fixture directory.

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


def _normalize_episode(data: dict[str, Any]) -> NumogramEpisode:
    """Normalize episode data from fixture."""
    episode_id = data["episode_id"]
    title = data["title"]
    summary_text = data["summary_text"]

    # Normalize whitespace
    summary_text = " ".join(summary_text.split())

    # Extract claims deterministically
    extracted_claims = _extract_claims(summary_text)

    # Extract temporal/diagram tokens
    extracted_tokens = _extract_tokens(summary_text)

    # Build provenance
    provenance = ProvenanceBundle(
        inputs=[
            ProvenanceRef(
                scheme="fixture",
                path=f"numogram/{episode_id}",
                sha256=hash_canonical_json(data),
            )
        ],
        transforms=["normalize_whitespace", "extract_claims", "extract_tokens"],
        metrics={"token_count": float(len(extracted_tokens))},
        created_by="numogram_corpus_loader",
    )

    return NumogramEpisode(
        episode_id=episode_id,
        title=title,
        summary_text=summary_text,
        extracted_claims=extracted_claims,
        extracted_tokens=extracted_tokens,
        phase="unfalsifiable_closure",  # Numogram episodes are terminal phase
        provenance=provenance,
    )


def _extract_claims(summary_text: str, max_claims: int = 5) -> list[str]:
    """Extract claims deterministically from summary text."""
    # Simple sentence split
    sentences = re.split(r'[.!?]+\s+', summary_text)

    claims = []
    for sent in sentences[:max_claims]:
        sent = sent.strip()
        if len(sent) > 10:
            claims.append(sent)

    return claims


def _extract_tokens(text: str) -> dict[str, int]:
    """Extract and count temporal authority tokens from text."""
    text_lower = text.lower()
    token_counts: dict[str, int] = {}

    # Check all lexemes from all categories
    for category, lexemes in TRIGGER_LEXICON.items():
        for lexeme in lexemes:
            count = text_lower.count(lexeme.lower())
            if count > 0:
                token_counts[lexeme] = count

    return token_counts


def build_numogram_casebook(episodes: list[NumogramEpisode]) -> NumogramCasebook:
    """
    Build NumogramCasebook from episodes.

    Args:
        episodes: List of episodes

    Returns:
        Complete NumogramCasebook
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
        transforms=["aggregate_numogram_episodes"],
        metrics={"episode_count": float(len(episodes))},
        created_by="numogram_casebook_builder",
    )

    return NumogramCasebook(
        casebook_id="NUMOGRAM_TT_CB",
        episodes=episodes,
        trigger_lexicon={cat: list(terms) for cat, terms in TRIGGER_LEXICON.items()},
        provenance=provenance,
    )
