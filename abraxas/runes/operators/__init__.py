"""ABX-Rune Operators.

This package contains operator implementations for each ABX-Rune.
Use the dispatch function for dynamic resolution.
"""

from .dispatch import dispatch

__all__ = ["dispatch"]
