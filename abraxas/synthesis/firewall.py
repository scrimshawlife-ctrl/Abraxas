"""Temporal Firewall - enforces TDD response modes at synthesis time."""

from __future__ import annotations

import re
from typing import Any

from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_string
from abraxas.temporal.lexicon import (
    MODAL_TERMS,
    AGENCY_TRANSFER,
    CLOSURE_TERMS,
    CAUSALITY_INVERSION,
    CERTAINTY_PATTERNS,
    METAPHOR_MARKERS,
    count_lexeme_matches,
    extract_lexeme_matches,
)
from abraxas.temporal.models import TemporalDriftResult, SovereigntyRisk


def compute_text_metrics(text: str) -> dict[str, float]:
    """
    Compute firewall metrics for text.

    Args:
        text: Text to analyze

    Returns:
        Dictionary of metric counts
    """
    return {
        "modal_verb_count": float(count_lexeme_matches(text, MODAL_TERMS)),
        "agency_transfer_count": float(count_lexeme_matches(text, AGENCY_TRANSFER)),
        "closure_term_count": float(count_lexeme_matches(text, CLOSURE_TERMS)),
        "causality_inversion_count": float(count_lexeme_matches(text, CAUSALITY_INVERSION)),
        "metaphor_count": float(count_lexeme_matches(text, METAPHOR_MARKERS)),
        "word_count": float(len(text.split())),
        "sentence_count": float(len([s for s in re.split(r'[.!?]+', text) if s.strip()])),
    }


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text (deterministic)."""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines with double newline
    text = re.sub(r'\n\n+', '\n\n', text)
    # Strip leading/trailing whitespace
    return text.strip()


def apply_contextualize(draft_text: str) -> tuple[str, list[str]]:
    """
    Apply CONTEXTUALIZE mode: prepend 1-line lens disclaimer.

    Args:
        draft_text: Original draft text

    Returns:
        Tuple of (modified_text, actions_taken)
    """
    disclaimer = "Note: The following represents one interpretive lens among many possible frameworks.\n\n"
    modified = disclaimer + draft_text
    actions = ["added_interpretive_lens_disclaimer"]
    return normalize_whitespace(modified), actions


def apply_pluralize(draft_text: str) -> tuple[str, list[str]]:
    """
    Apply PLURALIZE mode: append 3 alternative interpretations, strip strongest modals.

    Args:
        draft_text: Original draft text

    Returns:
        Tuple of (modified_text, actions_taken)
    """
    actions = []

    # Strip strongest modal terms
    modified = draft_text
    strongest_modals = ["inevitable", "inevitably", "destined", "must", "cannot", "always", "never"]
    for modal in strongest_modals:
        # Case-insensitive word boundary replacement
        pattern = r'\b' + re.escape(modal) + r'\b'
        if re.search(pattern, modified, re.IGNORECASE):
            modified = re.sub(pattern, '', modified, flags=re.IGNORECASE)
            actions.append(f"stripped_modal_{modal}")

    # Clean up any double spaces created by removals
    modified = re.sub(r' +', ' ', modified)

    # Append 3 alternative interpretations
    alternatives = """

Alternative interpretations:

1. This pattern may reflect structural similarities rather than causal relationships.

2. The observed correlations could emerge from shared underlying constraints rather than direct connections.

3. These elements might be better understood as parallel developments within a broader conceptual space."""

    modified = modified + alternatives
    actions.append("added_3_alternative_interpretations")

    return normalize_whitespace(modified), actions


def apply_de_escalate(draft_text: str) -> tuple[str, list[str]]:
    """
    Apply DE_ESCALATE mode: soften certainty, limit metaphors, add falsifiability nudge.

    Args:
        draft_text: Original draft text

    Returns:
        Tuple of (modified_text, actions_taken)
    """
    actions = []
    modified = draft_text

    # Replace certainty patterns with softer alternatives
    for pattern, replacement in CERTAINTY_PATTERNS:
        if re.search(pattern, modified, re.IGNORECASE):
            modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE)
            pattern_clean = pattern.strip('\\b')
            actions.append(f"softened_certainty_{pattern_clean}")

    # Limit to 1 metaphor maximum by removing metaphor markers after the first
    metaphor_positions = []
    modified_lower = modified.lower()
    for marker in METAPHOR_MARKERS:
        idx = 0
        while True:
            pos = modified_lower.find(marker.lower(), idx)
            if pos == -1:
                break
            metaphor_positions.append((pos, marker))
            idx = pos + 1

    # Sort by position and keep only first
    metaphor_positions.sort()
    if len(metaphor_positions) > 1:
        # Remove metaphor markers after the first (in reverse order to preserve indices)
        for pos, marker in reversed(metaphor_positions[1:]):
            # Remove the marker
            pattern = r'\b' + re.escape(marker) + r'\b'
            # Only remove one occurrence at a time
            modified = re.sub(pattern, '', modified, count=1, flags=re.IGNORECASE)
        actions.append(f"limited_metaphors_to_1_from_{len(metaphor_positions)}")

    # Add falsifiability nudge
    falsifiability_nudge = "\n\nWhat evidence would challenge this interpretation?"
    modified = modified + falsifiability_nudge
    actions.append("added_falsifiability_nudge")

    return normalize_whitespace(modified), actions


def apply_refuse_extension(draft_text: str) -> tuple[str, list[str]]:
    """
    Apply REFUSE_EXTENSION mode: output refusal template with short excerpt.

    Args:
        draft_text: Original draft text

    Returns:
        Tuple of (modified_text, actions_taken)
    """
    actions = ["refused_extension", "provided_grounded_alternatives"]

    # Extract short excerpt (max 40 words)
    words = draft_text.split()
    excerpt = ' '.join(words[:40])
    if len(words) > 40:
        excerpt += "..."

    refusal_template = f"""I notice this content contains patterns that may compromise epistemic sovereignty (temporal determinism, agency dissolution, or eschatological closure).

Excerpt from draft: "{excerpt}"

Instead, I can help with:

1. Analyzing the symbolic structure without asserting metaphysical claims
2. Exploring historical context of these conceptual frameworks
3. Comparing multiple interpretive approaches without privileging one
4. Examining methodological assumptions in the source material

Would you like me to focus on one of these grounded alternatives?"""

    return normalize_whitespace(refusal_template), actions


def apply_temporal_firewall(
    draft_text: str,
    tdd_result: TemporalDriftResult,
    context: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Apply temporal firewall transformations based on TDD result.

    Args:
        draft_text: Original draft text to transform
        tdd_result: Temporal drift detection result
        context: Optional context dictionary

    Returns:
        Tuple of (transformed_text, metadata_dict)
    """
    if context is None:
        context = {}

    # Normalize input text
    draft_text = normalize_whitespace(draft_text)

    # Compute pre-transformation metrics
    pre_metrics = compute_text_metrics(draft_text)

    # Determine response mode from TDD result
    # High/Critical sovereignty risk should trigger de-escalation or refusal
    if tdd_result.sovereignty_risk == SovereigntyRisk.CRITICAL:
        response_mode = "REFUSE_EXTENSION"
    elif tdd_result.sovereignty_risk == SovereigntyRisk.HIGH:
        response_mode = "DE_ESCALATE"
    elif tdd_result.sovereignty_risk == SovereigntyRisk.MODERATE:
        response_mode = "PLURALIZE"
    else:
        response_mode = "CONTEXTUALIZE"

    # Allow context override (for testing or explicit control)
    if "force_response_mode" in context:
        response_mode = context["force_response_mode"]

    # Apply appropriate transformation
    if response_mode == "CONTEXTUALIZE":
        transformed_text, actions = apply_contextualize(draft_text)
    elif response_mode == "PLURALIZE":
        transformed_text, actions = apply_pluralize(draft_text)
    elif response_mode == "DE_ESCALATE":
        transformed_text, actions = apply_de_escalate(draft_text)
    elif response_mode == "REFUSE_EXTENSION":
        transformed_text, actions = apply_refuse_extension(draft_text)
    else:
        # Fallback: no transformation
        transformed_text = draft_text
        actions = ["no_transformation"]

    # Compute post-transformation metrics
    post_metrics = compute_text_metrics(transformed_text)

    # Compute deltas
    delta = {
        key: post_metrics[key] - pre_metrics[key]
        for key in pre_metrics.keys()
    }

    # Build provenance
    provenance = ProvenanceBundle(
        inputs=[
            ProvenanceRef(
                scheme="text",
                path="draft_input",
                sha256=hash_string(draft_text),
            )
        ],
        transforms=[
            "temporal_firewall",
            f"response_mode_{response_mode}",
        ] + actions,
        metrics={
            "modal_delta": delta["modal_verb_count"],
            "agency_transfer_delta": delta["agency_transfer_count"],
            "closure_term_delta": delta["closure_term_count"],
        },
        created_by="temporal_firewall",
    )

    # Build metadata
    metadata = {
        "response_mode": response_mode,
        "firewall_actions": actions,
        "pre_metrics": pre_metrics,
        "post_metrics": post_metrics,
        "delta": delta,
        "provenance": provenance,
        "tdd_result": {
            "temporal_mode": tdd_result.temporal_mode.value,
            "causality_status": tdd_result.causality_status.value,
            "diagram_role": tdd_result.diagram_role.value,
            "sovereignty_risk": tdd_result.sovereignty_risk.value,
            "operator_hits": tdd_result.operator_hits,
        },
    }

    return transformed_text, metadata
