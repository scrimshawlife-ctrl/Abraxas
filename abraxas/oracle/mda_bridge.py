from __future__ import annotations

from typing import Any, Dict, Sequence, Tuple

from abraxas.mda.adapters.router import AdapterRouter
from abraxas.mda.registry import DomainRegistryV1
from abraxas.mda.run import run_mda
from abraxas.mda.types import MDARunEnvelope


def run_mda_for_oracle(
    *,
    env: str,
    run_at_iso: str,
    seed: int,
    abraxas_version: str,
    domains: Sequence[str],
    subdomains: Sequence[str],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Oracle bridge for MDA: deterministic, pure call path.

    This is intentionally thin: it uses the same adapter router and `run_mda`
    entrypoint as the CLI-equivalent direct path.
    """
    registry = DomainRegistryV1()
    router = AdapterRouter()
    adapted = router.adapt(payload, registry=registry)

    inputs = {"vectors": adapted.vectors, "adapter_notes": adapted.notes}
    envelope = MDARunEnvelope(
        env=str(env),
        run_at_iso=str(run_at_iso),
        seed=int(seed),
        promotion_enabled=False,
        enabled_domains=tuple(str(d) for d in domains),
        enabled_subdomains=tuple(str(s) for s in subdomains),
        inputs=inputs,
    )
    _, out = run_mda(envelope, abraxas_version=str(abraxas_version), registry=registry)
    return out

