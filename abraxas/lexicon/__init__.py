"""Lexicon Engine v1: Domain-scoped, versioned token-weight mapping."""

from .engine import (
    CompressionResult,
    InMemoryLexiconRegistry,
    LexiconEngine,
    LexiconEntry,
    LexiconPack,
    LexiconRegistry,
)

# PostgresLexiconRegistry is optional (requires psycopg)
try:
    from .pg_registry import PostgresLexiconRegistry

    __all__ = [
        "LexiconEntry",
        "LexiconPack",
        "LexiconRegistry",
        "InMemoryLexiconRegistry",
        "PostgresLexiconRegistry",
        "LexiconEngine",
        "CompressionResult",
    ]
except ImportError:
    __all__ = [
        "LexiconEntry",
        "LexiconPack",
        "LexiconRegistry",
        "InMemoryLexiconRegistry",
        "LexiconEngine",
        "CompressionResult",
    ]
