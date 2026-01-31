"""Synthesis Renderer - produces final output with temporal firewall integration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from abraxas.core.provenance import ProvenanceBundle
from abraxas.synthesis.firewall import apply_temporal_firewall
from abraxas.temporal.detector import analyze_text
from abraxas.temporal.models import TemporalDriftResult


class SynthesisResponse(BaseModel):
    """Response from synthesis renderer with firewall metadata."""

    final_text: str = Field(description="Final transformed text after firewall")
    draft_text: str = Field(description="Original draft text before firewall")
    firewall_applied: bool = Field(description="Whether firewall was applied")
    response_mode: str | None = Field(default=None, description="Firewall response mode used")
    tdd_result: TemporalDriftResult | None = Field(default=None, description="TDD analysis result")
    firewall_metadata: dict[str, Any] = Field(default_factory=dict, description="Firewall transformation metadata")
    provenance: ProvenanceBundle | None = Field(default=None, description="Provenance for synthesis")


class SynthesisRenderer:
    """
    Synthesis renderer with temporal firewall integration.

    Coordinates TDD analysis and firewall transformations for output generation.
    """

    def __init__(self, enable_firewall: bool = True):
        """
        Initialize renderer.

        Args:
            enable_firewall: Whether to enable temporal firewall (default True)
        """
        self.enable_firewall = enable_firewall

    def render(
        self,
        draft_text: str,
        context: dict[str, Any] | None = None,
        skip_tdd: bool = False,
        tdd_result: TemporalDriftResult | None = None,
    ) -> SynthesisResponse:
        """
        Render final output with temporal firewall.

        Args:
            draft_text: Draft text to render
            context: Optional context dictionary
            skip_tdd: Skip TDD analysis (requires tdd_result to be provided)
            tdd_result: Pre-computed TDD result (optional, will analyze if not provided)

        Returns:
            SynthesisResponse with final text and metadata
        """
        if context is None:
            context = {}

        # Run TDD analysis if not provided
        if tdd_result is None and not skip_tdd:
            tdd_result = analyze_text(draft_text)

        # Apply firewall if enabled and TDD result available
        if self.enable_firewall and tdd_result is not None:
            final_text, firewall_metadata = apply_temporal_firewall(
                draft_text=draft_text,
                tdd_result=tdd_result,
                context=context,
            )

            response = SynthesisResponse(
                final_text=final_text,
                draft_text=draft_text,
                firewall_applied=True,
                response_mode=firewall_metadata.get("response_mode"),
                tdd_result=tdd_result,
                firewall_metadata=firewall_metadata,
                provenance=firewall_metadata.get("provenance"),
            )
        else:
            # No firewall, return draft as-is
            response = SynthesisResponse(
                final_text=draft_text,
                draft_text=draft_text,
                firewall_applied=False,
                response_mode=None,
                tdd_result=tdd_result,
                firewall_metadata={},
                provenance=None,
            )

        return response

    def render_batch(
        self,
        drafts: list[str],
        context: dict[str, Any] | None = None,
    ) -> list[SynthesisResponse]:
        """
        Render multiple drafts with temporal firewall.

        Args:
            drafts: List of draft texts
            context: Optional context dictionary

        Returns:
            List of SynthesisResponse objects
        """
        return [self.render(draft, context=context) for draft in drafts]


# Convenience function
def render_with_firewall(
    draft_text: str,
    enable_firewall: bool = True,
    context: dict[str, Any] | None = None,
) -> SynthesisResponse:
    """
    Convenience function to render text with temporal firewall.

    Args:
        draft_text: Draft text to render
        enable_firewall: Whether to enable firewall
        context: Optional context dictionary

    Returns:
        SynthesisResponse with final text and metadata
    """
    renderer = SynthesisRenderer(enable_firewall=enable_firewall)
    return renderer.render(draft_text, context=context)
