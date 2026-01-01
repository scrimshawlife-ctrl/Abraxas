"""
Event Correlation (offline, shadow lane).

Public contract:
  correlate(envelopes: list[dict]) -> drift_report_v1 dict
"""

from .correlator import correlate

__all__ = ["correlate"]

