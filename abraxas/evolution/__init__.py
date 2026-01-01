"""
Evolution subsystem for Abraxas.

This module handles:
- Metric candidate generation from MW/AAlmanac/Integrity deltas
- Sandbox testing with score comparison
- Promotion gate with stabilization windows
- Parameter override management

IMPORTANT: This is NOT autonomous metric creation.
All candidates require sandbox proof and stabilization before promotion.
Metrics/operators create implementation tickets (manual review).
Only param tweaks auto-apply.
"""

__all__ = ["schema", "candidate_generator", "sandbox", "promotion_gate"]
