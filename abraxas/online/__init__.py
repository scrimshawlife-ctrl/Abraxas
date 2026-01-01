"""
Online subsystem for Abraxas.

This module handles:
- Source vector map registry (discovery, not scraping)
- Allowlist validation
- Cadence hints for schedulers

IMPORTANT: This does NOT do online scraping.
It only maps semantic nodes to existing OSH allowlist sources.
"""

__all__ = ["vector_map_loader"]
