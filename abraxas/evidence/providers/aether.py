"""Aether Evidence Provider (multimodal) — refuses per sibling Aether/SPEC.md.

This is the deliberate fail-closed boundary. Aether is intentionally PLANNED
and never available. See /Users/appliedalchemylabs/Aether/SPEC.md and
docs/SIBLING_REPOS.md.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType
from abraxas.evidence.provider import EvidenceProvider


class AetherNotImplemented(NotImplementedError):
    """Raised by the aether boundary to signal no implementation exists.

    Message must name missing components per sibling SPEC §3/§5.
    """
    pass

class AetherEvidenceProvider(EvidenceProvider):
    """Refusing implementation for aether (MULTIMODAL_INTEGRATION)."""

    @property
    def engine_name(self) -> str:
        return "aether"

    @property
    def engine_version(self) -> str:
        return "aether.multimodal.v0"

    @property
    def supported_evidence_types(self) -> List[EvidenceType]:
        return [EvidenceType.MULTIMODAL_INTEGRATION]

    def get_model_identity(self) -> str:
        raise AetherNotImplemented(
            "aether cannot produce model identity: implementation_status=not_implemented. "
            "Missing: per-modality encoders (text, image, audio, structured) — none exist; "
            "fusion policy; attribution layer; budget controller. "
            "See /Users/appliedalchemylabs/Aether/SPEC.md §3."
        )

    def produce_evidence(
        self,
        request_id: str,
        claim: str,
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None
    ) -> "EvidenceEnvelope":
        """Always raises — the point of this engine per sibling SPEC §5."""
        raise AetherNotImplemented(
            "aether cannot produce evidence: implementation_status=not_implemented. "
            "Missing: per-modality encoders (text, image, audio, structured) — none exist; "
            "fusion policy; attribution layer; budget controller. "
            "See /Users/appliedalchemylabs/Aether/SPEC.md §3 and §4 (no confidence laundering, "
            "per-modality provenance, fail closed on missing modalities)."
        )

def create_aether_adapter() -> EvidenceProvider:
    return AetherEvidenceProvider()
