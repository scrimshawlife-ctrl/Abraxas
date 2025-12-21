"""Tests for Lexicon Engine v1."""

import pytest

from abraxas.lexicon.engine import (
    InMemoryLexiconRegistry,
    LexiconEngine,
    LexiconEntry,
    LexiconPack,
)


def test_lexicon_compress_is_deterministic():
    """Test that lexicon compression is deterministic."""
    reg = InMemoryLexiconRegistry()
    pack = LexiconPack(
        domain="slang",
        version="1.0.0",
        entries=(
            LexiconEntry("cap", 0.9, {"tag": "negation"}),
            LexiconEntry("no_cap", 1.1, {"tag": "assertion"}),
        ),
        created_at_utc="2025-12-20T00:00:00Z",
    )
    reg.register(pack)

    eng = LexiconEngine(reg)
    res = eng.compress("slang", ["cap", "unknown", "no_cap"], run_id="RUN-1")

    assert res.matched == ("cap", "no_cap")
    assert res.unmatched == ("unknown",)
    assert res.weights_out == {"cap": 0.9, "no_cap": 1.1}
    assert res.provenance.run_id == "RUN-1"


def test_lexicon_registry_versioning():
    """Test that lexicon registry handles versioning correctly."""
    reg = InMemoryLexiconRegistry()

    pack_v1 = LexiconPack(
        domain="slang",
        version="1.0.0",
        entries=(LexiconEntry("cap", 0.9, {}),),
        created_at_utc="2025-12-20T00:00:00Z",
    )

    pack_v2 = LexiconPack(
        domain="slang",
        version="2.0.0",
        entries=(LexiconEntry("cap", 1.2, {}), LexiconEntry("bussin", 1.5, {})),
        created_at_utc="2025-12-21T00:00:00Z",
    )

    reg.register(pack_v1)
    reg.register(pack_v2)

    # Latest should return v2
    latest = reg.latest("slang")
    assert latest is not None
    assert latest.version == "2.0.0"

    # Explicit version should work
    v1 = reg.get("slang", "1.0.0")
    assert v1 is not None
    assert v1.version == "1.0.0"
    assert len(v1.entries) == 1

    # List versions
    versions = reg.list_versions("slang")
    assert versions == ["1.0.0", "2.0.0"]


def test_lexicon_engine_resolve():
    """Test lexicon pack resolution."""
    reg = InMemoryLexiconRegistry()
    pack = LexiconPack(
        domain="idiom",
        version="1.0.0",
        entries=(LexiconEntry("break_the_ice", 1.0, {}),),
        created_at_utc="2025-12-20T00:00:00Z",
    )
    reg.register(pack)

    eng = LexiconEngine(reg)

    # Should resolve latest by default
    resolved = eng.resolve("idiom")
    assert resolved.version == "1.0.0"

    # Should resolve specific version
    resolved = eng.resolve("idiom", "1.0.0")
    assert resolved.version == "1.0.0"

    # Should raise on missing domain
    with pytest.raises(KeyError):
        eng.resolve("nonexistent")


def test_lexicon_compression_preserves_order():
    """Test that compression preserves input token order."""
    reg = InMemoryLexiconRegistry()
    pack = LexiconPack(
        domain="test",
        version="1.0.0",
        entries=(
            LexiconEntry("a", 1.0, {}),
            LexiconEntry("b", 2.0, {}),
            LexiconEntry("c", 3.0, {}),
        ),
        created_at_utc="2025-12-20T00:00:00Z",
    )
    reg.register(pack)

    eng = LexiconEngine(reg)

    # Order should match input order, not lexicon order
    res = eng.compress("test", ["c", "a", "b", "unknown", "a"], run_id="RUN-1")

    assert res.tokens_in == ("c", "a", "b", "unknown", "a")
    assert res.matched == ("c", "a", "b", "a")
    assert res.unmatched == ("unknown",)


def test_lexicon_compression_provenance():
    """Test that compression includes proper provenance."""
    reg = InMemoryLexiconRegistry()
    pack = LexiconPack(
        domain="test",
        version="1.0.0",
        entries=(LexiconEntry("word", 1.0, {}),),
        created_at_utc="2025-12-20T00:00:00Z",
    )
    reg.register(pack)

    eng = LexiconEngine(reg)
    res = eng.compress("test", ["word"], run_id="TEST-123", git_sha="abc123", host="test-host")

    assert res.provenance.run_id == "TEST-123"
    assert res.provenance.git_sha == "abc123"
    assert res.provenance.host == "test-host"
    assert res.provenance.inputs_hash is not None
    assert res.provenance.config_hash is not None


def test_lexicon_empty_tokens():
    """Test compression with empty token list."""
    reg = InMemoryLexiconRegistry()
    pack = LexiconPack(
        domain="test",
        version="1.0.0",
        entries=(LexiconEntry("word", 1.0, {}),),
        created_at_utc="2025-12-20T00:00:00Z",
    )
    reg.register(pack)

    eng = LexiconEngine(reg)
    res = eng.compress("test", [], run_id="RUN-1")

    assert res.matched == ()
    assert res.unmatched == ()
    assert res.weights_out == {}


def test_lexicon_all_unmatched():
    """Test compression with no matching tokens."""
    reg = InMemoryLexiconRegistry()
    pack = LexiconPack(
        domain="test",
        version="1.0.0",
        entries=(LexiconEntry("word", 1.0, {}),),
        created_at_utc="2025-12-20T00:00:00Z",
    )
    reg.register(pack)

    eng = LexiconEngine(reg)
    res = eng.compress("test", ["unknown1", "unknown2"], run_id="RUN-1")

    assert res.matched == ()
    assert res.unmatched == ("unknown1", "unknown2")
    assert res.weights_out == {}
