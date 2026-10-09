"""Semion Evidence Provider for SIGN_RELATION (planned minimal stub)."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.evidence.contract import EvidenceType
from abraxas.evidence.provider import EvidenceProvider


class SemionEvidenceProvider(EvidenceProvider):
    """Minimal stub for semion (SIGN_RELATION).

    Follows the EvidenceProvider interface for manifest agreement.
    """

    @property
    def engine_name(self) -> str:
        return "semion"

    @property
    def engine_version(self) -> str:
        return "semion.sign.v0"

    @property
    def supported_evidence_types(self) -> List[EvidenceType]:
        return [EvidenceType.SIGN_RELATION]

    def provide(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return {
            "engine": "semion",
            "status": "planned-stub",
            "version": self.engine_version,
        }


def create_semion_adapter() -> EvidenceProvider:
    """Factory for manifest."""
    return SemionEvidenceProvider()
