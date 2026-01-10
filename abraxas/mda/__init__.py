"""MDA (Memetic Drift Analysis) package.

This package is intentionally lightweight and self-contained. It provides:
- Deterministic projection of MDA outputs into Oracle Signal Layer v2 slices.
- A small CLI entrypoint (`python -m abraxas.mda`) for emitting artifacts.
- Minimal MDA sandbox helpers and wiring utilities.
"""

from __future__ import annotations

__all__ = [
    "run_mda",
]

from .run import run_mda
