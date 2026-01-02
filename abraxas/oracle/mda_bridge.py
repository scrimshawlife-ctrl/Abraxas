from __future__ import annotations

"""
Oracle → MDA bridge (stub)

Purpose: allow Oracle to invoke MDA without coupling to CLI, fixtures, or sandbox paths.
This file is intentionally tiny and stable.

Contract:
  - caller provides envelope fields and canonical inputs (or vectors via adapter router)
  - returns the MDA payload dict (envelope + dsp + fusion_graph + aggregates)
"""

from typing import Any, Dict, Optional, Tuple

from abraxas.mda.registry import DomainRegistryV1
from abraxas.mda.types import MDARunEnvelope
from abraxas.mda.run import run_mda
from abraxas.mda.adapters.router import AdapterRouter


def run_mda_for_oracle(
    *,
    env: str,
    run_at_iso: str,
    seed: int,
    abraxas_version: str,
    domains: Optional[Tuple[str, ...]] = None,
    subdomains: Optional[Tuple[str, ...]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    reg = DomainRegistryV1()
    enabled_domains = domains if domains is not None else tuple(reg.domains())
    enabled_subdomains = subdomains if subdomains is not None else tuple(reg.all_subdomain_keys())

    inputs: Dict[str, Any] = {}
    if payload:
        # Adapt payload into vectors if it contains vectors/bundle
        router = AdapterRouter()
        adapted = router.adapt(payload, registry=reg)
        inputs["vectors"] = adapted.vectors
        inputs["adapter_notes"] = adapted.notes

    envelope = MDARunEnvelope(
        env=env,
        run_at_iso=run_at_iso,
        seed=seed,
        promotion_enabled=False,
        enabled_domains=enabled_domains,
        enabled_subdomains=enabled_subdomains,
        inputs=inputs,
    )

    _, out = run_mda(envelope, abraxas_version=abraxas_version, registry=reg)
    return out

