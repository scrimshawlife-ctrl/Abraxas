from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import AdapterResult
from ..registry import DomainRegistryV1


@dataclass(frozen=True)
class EvidenceBundleAdapter:
    """
    Evidence bundle adapter v1.

    Expected payload shape:
      {"bundle_id": "...", "vectors": {<domain>: {<subdomain>: {...}}}}
    """

    name: str = "evidence_bundle_v1"

    def adapt(self, payload: Dict[str, Any], *, registry: DomainRegistryV1) -> AdapterResult:
        vectors = payload.get("vectors")
        if not isinstance(vectors, dict):
            return AdapterResult(vectors={}, notes="evidence_bundle_v1: missing/invalid vectors; vectors={}")

        # Deterministic filtering to registry-known domains/subdomains only.
        out: Dict[str, Any] = {}
        for domain in registry.domains():
            dom_payload = vectors.get(domain)
            if not isinstance(dom_payload, dict):
                continue
            kept_subs: Dict[str, Any] = {}
            for sub in registry.subdomains(domain):
                if sub in dom_payload:
                    kept_subs[sub] = dom_payload[sub]
            if kept_subs:
                out[domain] = kept_subs

        notes = f"evidence_bundle_v1: bundle_id={payload.get('bundle_id','')}"
        return AdapterResult(vectors=out, notes=notes)

