from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AdaptedPayload:
    vectors: Dict[str, Dict[str, Any]]
    notes: List[str]
    route: str


class AdapterRouter:
    """
    Minimal deterministic adapter router for the Oracle MDA bridge canary.

    Routing:
      - vectors_only_v1: payload has top-level "vectors"
      - evidence_bundle_v1: payload has top-level "evidence_bundle" with nested "vectors"
    """

    def adapt(self, payload: Dict[str, Any], *, registry: Optional[object] = None) -> AdaptedPayload:
        # registry is accepted for parity with future adapters; unused here.
        if isinstance(payload.get("vectors"), dict):
            return AdaptedPayload(
                vectors=payload.get("vectors", {}) or {},
                notes=["adapter_route=vectors_only_v1"],
                route="vectors_only_v1",
            )

        eb = payload.get("evidence_bundle")
        if isinstance(eb, dict) and isinstance(eb.get("vectors"), dict):
            notes: List[str] = ["adapter_route=evidence_bundle_v1"]
            for n in (eb.get("notes") or []):
                if str(n).strip():
                    notes.append(str(n))
            return AdaptedPayload(
                vectors=eb.get("vectors", {}) or {},
                notes=notes,
                route="evidence_bundle_v1",
            )

        return AdaptedPayload(vectors={}, notes=["adapter_route=unknown"], route="unknown")

