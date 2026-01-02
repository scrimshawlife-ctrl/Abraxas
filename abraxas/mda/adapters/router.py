from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import AdapterResult
from .evidence_bundle import EvidenceBundleAdapter
from ..registry import DomainRegistryV1


@dataclass(frozen=True)
class AdapterRouter:
    """
    Deterministic adapter selection.
    No I/O, no time, no randomness, no network.
    """

    evidence_bundle: EvidenceBundleAdapter = EvidenceBundleAdapter()

    def detect(self, payload: Dict[str, Any]) -> str:
        # Evidence bundle signature: {"bundle_id":..., "vectors":{...}}
        if isinstance(payload.get("vectors"), dict) and ("bundle_id" in payload):
            return self.evidence_bundle.name
        # Canon vectors-only signature: {"vectors":{...}}
        if isinstance(payload.get("vectors"), dict):
            return "vectors_only_v1"
        return "unknown"

    def adapt(self, payload: Dict[str, Any], *, registry: DomainRegistryV1) -> AdapterResult:
        kind = self.detect(payload)
        if kind == self.evidence_bundle.name:
            return self.evidence_bundle.adapt(payload, registry=registry)
        if kind == "vectors_only_v1":
            # Normalize via the evidence bundle adapter by wrapping.
            wrapped = {"bundle_id": "vectors_only", "vectors": payload.get("vectors") or {}}
            return self.evidence_bundle.adapt(wrapped, registry=registry)
        # Unknown payload => empty vectors, deterministic
        return AdapterResult(vectors={}, notes="adapter_router: unknown payload; vectors={} (not_computable expected)")

