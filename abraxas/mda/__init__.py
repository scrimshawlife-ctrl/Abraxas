"""
MDA (Minimal Deterministic Adapter) subsystem.

This package is intentionally small and deterministic:
- no network
- no time reads
- no randomness without an explicit seed
"""

from __future__ import annotations

