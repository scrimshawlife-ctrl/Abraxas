from __future__ import annotations

from typing import Dict

NON_CENSORSHIP_INVARIANT = (
    "Abraxas MUST NEVER censor, filter, rewrite, or block user-facing outputs. "
    "Detectors may only flag or log potential drift; they must never edit what is shown to users."
)

BANNED_BEHAVIORS = [
    "firewalls that strip or rewrite responses",
    "moderation hooks that redact or sanitize outputs",
    "rewrite filters that alter user-facing phrasing",
    "blocking or refusal branches that replace model text",
    "disclaimer or safety prefaces appended to responses",
]


class NonCensorshipViolation(RuntimeError):
    """Raised when rendered output deviates from the model draft."""


def normalize_for_comparison(text: str) -> str:
    """
    Canonicalize text for safe comparison without hiding semantic drift.

    Only trailing whitespace removal and newline normalization are permitted to
    avoid masking rewrites.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
    return normalized.rstrip("\n")


def assert_output_unchanged(original: str, rendered: str, context: Dict) -> None:
    """Ensure the rendered output exactly matches the draft text."""
    normalized_original = normalize_for_comparison(original)
    normalized_rendered = normalize_for_comparison(rendered)
    if normalized_original != normalized_rendered:
        ctx_label = f" context={context!r}" if context else ""
        raise NonCensorshipViolation(
            f"Non-censorship invariant violated{ctx_label}: draft and rendered text diverge.",
        )
