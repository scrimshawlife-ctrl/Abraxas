"""Boundary and interface hardening primitives (Pass 13)."""

from abx.boundary.inputEnvelope import build_input_envelope
from abx.boundary.normalization import normalize_envelope
from abx.boundary.scorecard import build_boundary_health_scorecard
from abx.boundary.trustEnforcement import enforce_trust_for_authoritative_mutation
from abx.boundary.validation import validate_envelope

__all__ = [
    "build_input_envelope",
    "validate_envelope",
    "normalize_envelope",
    "enforce_trust_for_authoritative_mutation",
    "build_boundary_health_scorecard",
]
