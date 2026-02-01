"""Correlation Engine v1: Deterministic cross-domain correlation detection."""

from .engine import (
    CorrelationConfig,
    CorrelationEngine,
    CorrelationEvent,
    CorrelationResult,
)

__all__ = [
    "CorrelationEngine",
    "CorrelationEvent",
    "CorrelationConfig",
    "CorrelationResult",
]
