"""
Abraxas Multi-Domain Analysis (MDA)

Canon: MDA v1.1 (Hierarchical Subdomains)
- Domain -> Subdomain -> Signal Units
- Uniform DSP contract
- Evidence-gated; missing inputs => not_computable
- Deterministic provenance + invariance support
"""

from .registry import DomainRegistryV1
from .types import (
    Domain,
    DomainSignalPack,
    DSPStatus,
    EdgeType,
    FusionGraph,
    MDARunEnvelope,
)

__all__ = [
    "Domain",
    "DomainSignalPack",
    "DSPStatus",
    "EdgeType",
    "FusionGraph",
    "MDARunEnvelope",
    "DomainRegistryV1",
]

