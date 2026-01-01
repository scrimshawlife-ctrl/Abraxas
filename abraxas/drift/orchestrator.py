from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from abraxas.core.provenance import ProvenanceBundle, hash_string


class DriftFlag(BaseModel):
    """Describes a potential drift indicator without altering content."""

    code: str
    description: str
    positions: List[int] = Field(default_factory=list)


class DriftReport(BaseModel):
    """Structured drift metadata for a rendered text."""

    text_sha256: str
    provenance: ProvenanceBundle
    flags: List[DriftFlag] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    def has_flags(self) -> bool:
        return len(self.flags) > 0


_DRIFT_PATTERNS = {
    "filtered_marker": "filtered",
    "redaction_marker": "redacted",
    "moderation_marker": "content warning",
    "rewrite_marker": "[rewritten]",
}


def analyze_text_for_drift(text: str, provenance: ProvenanceBundle) -> DriftReport:
    """
    Analyze text for drift indicators.

    Returns metadata only; the caller is responsible for rendering logic.
    """
    lower = text.lower()
    flags: List[DriftFlag] = []
    for code, marker in _DRIFT_PATTERNS.items():
        if marker in lower:
            positions = [i for i in range(len(lower)) if lower.startswith(marker, i)]
            flags.append(
                DriftFlag(
                    code=code,
                    description=f"Detected marker '{marker}' that may indicate upstream rewriting or censorship.",
                    positions=positions,
                )
            )

    notes: List[str] = []
    if not text.strip():
        notes.append("Empty output encountered; verify upstream synthesis produced content.")

    return DriftReport(
        text_sha256=hash_string(text),
        provenance=provenance,
        flags=flags,
        notes=notes,
    )
