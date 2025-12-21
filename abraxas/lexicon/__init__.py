"""Lexicon Engine v1: Domain-scoped, versioned token-weight mapping."""

from .engine import (
    CompressionResult,
    InMemoryLexiconRegistry,
    LexiconEngine,
    LexiconEntry,
    LexiconPack,
    LexiconRegistry,
)

__all__ = [
    "LexiconEntry",
    "LexiconPack",
    "LexiconRegistry",
    "InMemoryLexiconRegistry",
    "LexiconEngine",
    "CompressionResult",
]
