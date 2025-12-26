"""
Abraxas Metrics Module

Provides standardized function exports for AAL-core integration.
Includes metric emergence and shadow evaluation system.
"""

from abraxas.metrics.alive import compute_alive
from abraxas.metrics.emergence import MetricEmergence
from abraxas.metrics.evidence import EvidenceBundle

__all__ = [
    "compute_alive",
    "MetricEmergence",
    "EvidenceBundle",
]
