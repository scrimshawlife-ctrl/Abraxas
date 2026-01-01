"""Rune definition models for ABX-Runes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RuneDefinition(BaseModel):
    """Complete definition of an ABX-Rune."""

    id: str = Field(..., description="Rune ID (e.g., 'ϟ₁')")
    name: str = Field(..., description="Full name of the rune")
    short_name: str = Field(..., description="Short name/acronym (e.g., 'RFA')")
    layer: str = Field(..., description="Layer: Core, Validation, Governance, etc.")
    motto: str = Field(..., description="Rune motto/principle")
    function: str = Field(..., description="Primary function description")
    inputs: list[str] = Field(default_factory=list, description="Input types/signals")
    outputs: list[str] = Field(default_factory=list, description="Output types/signals")
    constraints: list[str] = Field(default_factory=list, description="Operational constraints")
    hooks: list[str] = Field(default_factory=list, description="System hooks/integration points")
    evidence_tier: str = Field(default="canonical", description="Evidence tier: canonical, staging, experimental")
    provenance_sources: list[str] = Field(default_factory=list, description="Provenance source references")
    canonical_statement: str = Field(..., description="Canonical statement defining the rune")
    introduced_version: str = Field(..., description="Version when introduced")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def get_seed_material(self) -> str:
        """Get deterministic seed material for sigil generation."""
        return f"{self.id}:{self.short_name}:{self.introduced_version}:{self.canonical_statement}"


class SigilManifestEntry(BaseModel):
    """Single entry in sigil manifest."""

    id: str = Field(..., description="Rune ID")
    short_name: str = Field(..., description="Rune short name")
    svg_path: str = Field(..., description="Path to SVG file relative to repo root")
    sha256: str = Field(..., description="SHA256 hash of SVG file")
    seed_material: str = Field(..., description="Seed material used for generation")
    width: int = Field(default=512, description="SVG width")
    height: int = Field(default=512, description="SVG height")


class SigilManifest(BaseModel):
    """Manifest tracking all generated sigils."""

    generated_at_utc: str = Field(..., description="UTC timestamp of generation")
    generator_version: str = Field(..., description="Generator version")
    entries: list[SigilManifestEntry] = Field(default_factory=list, description="Sigil entries")
