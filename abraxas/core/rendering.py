from __future__ import annotations

from typing import Any, Dict

from abraxas.policy.non_censorship import assert_output_unchanged


def render_output(draft_text: str, *, context: Dict[str, Any] | None = None) -> str:
    """
    Final rendering boundary: return the draft verbatim while enforcing invariants.

    Any content changes must be surfaced as violations rather than silently applied.
    """
    rendered_text = draft_text
    assert_output_unchanged(draft_text, rendered_text, context or {})
    return rendered_text
