"""Deterministic tokenization tests."""

from __future__ import annotations

from abraxas.linguistics.normalize import tokenize


def test_tokenize_deterministic():
    text = "Hello, World! Hello?"
    tokens = tokenize(text)
    assert tokens == ["hello", "world", "hello"]
