"""Data models for Numogram Theory-Topology Casebook."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from abraxas.core.provenance import ProvenanceBundle


class NumogramEpisode(BaseModel):
    """A single episode in the Numogram TT-CB series."""

    episode_id: str = Field(..., description="Episode identifier (e.g., 'numogram_08')")
    title: str = Field(..., description="Episode title")
    summary_text: str = Field(..., description="Full episode summary")
    extracted_claims: list[str] = Field(
        default_factory=list,
        description="Key claims extracted from summary",
    )
    extracted_tokens: dict[str, int] = Field(
        default_factory=dict,
        description="Temporal/diagram authority tokens",
    )
    phase: str = Field(default="unfalsifiable_closure", description="Episode phase")
    provenance: ProvenanceBundle = Field(..., description="Episode provenance")


class NumogramCasebook(BaseModel):
    """Complete Numogram TT-CB casebook."""

    casebook_id: str = Field(default="NUMOGRAM_TT_CB", description="Casebook identifier")
    episodes: list[NumogramEpisode] = Field(default_factory=list, description="All episodes")
    trigger_lexicon: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Lexeme groups for temporal authority",
    )
    provenance: ProvenanceBundle = Field(..., description="Casebook provenance")
