"""Abraxas Metric Governance

Strict, anti-hallucination governance system for emergent metrics.

NON-NEGOTIABLE LAWS:
1. Metrics are Contracts, not Ideas
2. Candidate-First Lifecycle
3. Promotion Requires Evidence Bundle
4. Complexity Pays Rent
5. Stabilization Window Required

PROMOTION GATES (all required):
- Provenance Gate
- Falsifiability Gate
- Non-Redundancy Gate
- Rent-Payment Gate
- Ablation Gate
- Stabilization Gate
"""

from abraxas.metrics.governance import (
    CandidateMetric,
    CandidateStatus,
    EvidenceBundle,
    PromotionDecision,
    PromotionLedgerEntry,
)
from abraxas.metrics.evaluate import MetricEvaluator
from abraxas.metrics.registry_io import (
    CandidateRegistry,
    PromotionLedger,
    promote_candidate_to_canonical,
)
from abraxas.metrics.hashutil import hash_json, verify_hash_chain

__all__ = [
    # Core types
    "CandidateMetric",
    "CandidateStatus",
    "EvidenceBundle",
    "PromotionDecision",
    "PromotionLedgerEntry",
    # Evaluation
    "MetricEvaluator",
    # Registries
    "CandidateRegistry",
    "PromotionLedger",
    "promote_candidate_to_canonical",
    # Utilities
    "hash_json",
    "verify_hash_chain",
]
