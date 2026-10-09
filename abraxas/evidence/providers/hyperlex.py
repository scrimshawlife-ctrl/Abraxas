"""Hyperlex Evidence Provider for LEXICAL_SEMANTIC (planned minimal stub)."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.evidence.contract import EvidenceType
from abraxas.evidence.provider import EvidenceProvider


class HyperlexEvidenceProvider(EvidenceProvider):
    """Minimal stub for hyperlex (LEXICAL_SEMANTIC).

    Follows the EvidenceProvider interface for manifest agreement.
    """

    @property
    def engine_name(self) -> str:
        return "hyperlex"

    @property
    def engine_version(self) -> str:
        return "hyperlex.lexical.v0"

    @property
    def supported_evidence_types(self) -> List[EvidenceType]:
        return [EvidenceType.LEXICAL_SEMANTIC]

    def provide(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return {
            "engine": "hyperlex",
            "status": "planned-stub",
            "version": self.engine_version,
        }


def create_hyperlex_adapter() -> EvidenceProvider:
    """Factory for manifest."""
    return HyperlexEvidenceProvider()
