"""
SDCT v0.1 Test Suite

Tests for the Symbolic Domain Cartridge Template system.
Validates:
- Type contracts
- Cartridge protocol
- Registry functionality
- TextSubwordCartridge (Cartridge #0)
- DigitMotifCartridge (proof cartridge)
- Determinism guarantees
"""
from __future__ import annotations

import pytest
from typing import List

from abraxas_ase.domains import (
    # Types
    AggregatedMotifStats,
    DomainDescriptor,
    LANE_NAMES,
    LANE_ORDER,
    Motif,
    NormalizedEvidence,
    RawItem,
    lane_index,
    lane_name,
    # Protocol
    BaseCartridge,
    SymbolicDomainCartridge,
    # Registry
    DomainRegistry,
    get_default_registry,
    reset_default_registry,
    # Cartridges
    TextSubwordCartridge,
    DigitMotifCartridge,
    create_text_subword_cartridge,
    create_digit_cartridge,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_item() -> RawItem:
    """Sample item for testing."""
    return RawItem(
        id="test-001",
        source="reuters",
        published_at="2026-01-24T12:00:00Z",
        title="TRADE WAR ESCALATES: TARIFFS ANNOUNCED",
        text="The trade negotiations collapsed today after new tariffs were announced. "
        "Leaders declared a state of emergency as markets crashed. War of words "
        "continues with no peace in sight. Year 2024 marks a turning point.",
        url="https://example.com/article",
    )


@pytest.fixture
def digit_item() -> RawItem:
    """Sample item with digit patterns for testing."""
    return RawItem(
        id="digit-001",
        source="test",
        published_at="2026-01-24T12:00:00Z",
        title="1984 Predictions for 2024",
        text="The year 1776 was significant. In 2001, events unfolded. "
        "Phone: 555-1234. Reference number: 911. Code: 666.",
        url=None,
    )


@pytest.fixture
def text_cartridge() -> TextSubwordCartridge:
    """Text subword cartridge for testing."""
    return TextSubwordCartridge()


@pytest.fixture
def digit_cartridge() -> DigitMotifCartridge:
    """Digit motif cartridge for testing."""
    return DigitMotifCartridge()


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset default registry before each test."""
    reset_default_registry()
    yield
    reset_default_registry()


# -----------------------------------------------------------------------------
# Type Tests
# -----------------------------------------------------------------------------


class TestDomainDescriptor:
    """Tests for DomainDescriptor."""

    def test_creation(self):
        desc = DomainDescriptor(
            domain_id="test.v1",
            domain_name="Test Domain",
            domain_version="1.0.0",
            motif_kind="test",
            alphabet="a-z",
            constraints=frozenset(["constraint1"]),
            params_schema_id=None,
        )
        assert desc.domain_id == "test.v1"
        assert desc.domain_version == "1.0.0"

    def test_to_dict(self):
        desc = DomainDescriptor(
            domain_id="test.v1",
            domain_name="Test Domain",
            domain_version="1.0.0",
            motif_kind="test",
            alphabet="a-z",
            constraints=frozenset(["b", "a"]),  # Unordered
            params_schema_id=None,
        )
        d = desc.to_dict()
        assert d["domain_id"] == "test.v1"
        assert d["constraints"] == ["a", "b"]  # Sorted in output

    def test_content_hash_determinism(self):
        desc1 = DomainDescriptor(
            domain_id="test.v1",
            domain_name="Test",
            domain_version="1.0.0",
            motif_kind="test",
            alphabet="a-z",
            constraints=frozenset(["a", "b"]),
        )
        desc2 = DomainDescriptor(
            domain_id="test.v1",
            domain_name="Test",
            domain_version="1.0.0",
            motif_kind="test",
            alphabet="a-z",
            constraints=frozenset(["b", "a"]),  # Different order
        )
        assert desc1.content_hash() == desc2.content_hash()


class TestMotif:
    """Tests for Motif."""

    def test_creation(self):
        motif = Motif(
            domain_id="test.v1",
            motif_id="test.v1:war",
            motif_text="war",
            motif_len=3,
            motif_complexity=0.5,
            lane_hint="core",
        )
        assert motif.motif_text == "war"
        assert motif.lane_hint == "core"

    def test_to_dict(self):
        motif = Motif(
            domain_id="test.v1",
            motif_id="test.v1:war",
            motif_text="war",
            motif_len=3,
            motif_complexity=0.5,
            lane_hint="core",
            metadata={"tap": 1.2},
        )
        d = motif.to_dict()
        assert d["motif_text"] == "war"
        assert d["metadata"]["tap"] == 1.2


class TestNormalizedEvidence:
    """Tests for NormalizedEvidence."""

    def test_creation(self):
        ev = NormalizedEvidence(
            domain_id="test.v1",
            motif_id="test.v1:war",
            item_id="item-1",
            source="reuters",
            event_key="cluster-1",
            mentions=1,
            signals={"tap": 1.2},
            tags={"lane": "core"},
        )
        assert ev.domain_id == "test.v1"
        assert ev.signals["tap"] == 1.2

    def test_to_dict(self):
        ev = NormalizedEvidence(
            domain_id="test.v1",
            motif_id="test.v1:war",
            item_id="item-1",
            source="reuters",
            event_key="cluster-1",
            mentions=1,
        )
        d = ev.to_dict()
        assert d["domain_id"] == "test.v1"
        assert d["mentions"] == 1


class TestRawItem:
    """Tests for RawItem."""

    def test_from_dict(self):
        d = {
            "id": "test-1",
            "source": "reuters",
            "published_at": "2026-01-24T00:00:00Z",
            "title": "Test Title",
            "text": "Test text content",
            "url": "https://example.com",
        }
        item = RawItem.from_dict(d)
        assert item.id == "test-1"
        assert item.source == "reuters"
        assert item.url == "https://example.com"

    def test_to_dict(self):
        item = RawItem(
            id="test-1",
            source="reuters",
            published_at="2026-01-24T00:00:00Z",
            title="Test Title",
            text="Test text content",
        )
        d = item.to_dict()
        assert "url" not in d  # None values excluded


class TestLaneHelpers:
    """Tests for lane helper functions."""

    def test_lane_order(self):
        assert LANE_ORDER["candidate"] == 0
        assert LANE_ORDER["shadow"] == 1
        assert LANE_ORDER["canary"] == 2
        assert LANE_ORDER["core"] == 3

    def test_lane_index(self):
        assert lane_index("candidate") == 0
        assert lane_index("core") == 3
        assert lane_index("unknown") == 0  # Default

    def test_lane_name(self):
        assert lane_name(0) == "candidate"
        assert lane_name(3) == "core"
        assert lane_name(99) == "candidate"  # Default


# -----------------------------------------------------------------------------
# TextSubwordCartridge Tests
# -----------------------------------------------------------------------------


class TestTextSubwordCartridge:
    """Tests for TextSubwordCartridge."""

    def test_descriptor(self, text_cartridge):
        desc = text_cartridge.descriptor()
        assert desc.domain_id == "text.subword.v1"
        assert desc.motif_kind == "subword"
        assert desc.alphabet == "a-z"
        assert "alpha_only" in desc.constraints

    def test_encode(self, text_cartridge, sample_item):
        symbol = text_cartridge.encode(sample_item)
        assert symbol.item_id == sample_item.id
        assert symbol.source == sample_item.source
        assert len(symbol.tokens) > 0

        # Tokens should be sorted deterministically
        tokens = [t.token for t in symbol.tokens]
        assert tokens == sorted(tokens, key=lambda t: (
            text_cartridge._letters_sorted(t), t
        ))

    def test_extract_motifs(self, text_cartridge, sample_item):
        symbol = text_cartridge.encode(sample_item)
        motifs = text_cartridge.extract_motifs(symbol)

        assert len(motifs) > 0

        # Check motif structure
        for m in motifs:
            assert m.domain_id == "text.subword.v1"
            assert m.motif_id.startswith("text.subword.v1:")
            assert m.lane_hint in ["core", "canary"]

        # Should find some core subwords from the sample
        motif_texts = [m.motif_text for m in motifs]
        # "war" should be found in "TRADE WAR"
        assert "war" in motif_texts or "trade" in motif_texts

    def test_emit_evidence(self, text_cartridge, sample_item):
        symbol = text_cartridge.encode(sample_item)
        motifs = text_cartridge.extract_motifs(symbol)
        evidence = text_cartridge.emit_evidence(sample_item, motifs, "cluster-001")

        assert len(evidence) > 0

        for ev in evidence:
            assert ev.domain_id == "text.subword.v1"
            assert ev.item_id == sample_item.id
            assert ev.source == sample_item.source
            assert ev.event_key == "cluster-001"
            assert ev.mentions == 1
            assert "lane" in ev.tags

    def test_process_item_pipeline(self, text_cartridge, sample_item):
        """Test the full pipeline via process_item."""
        evidence = text_cartridge.process_item(sample_item, "cluster-test")
        assert len(evidence) > 0
        assert all(ev.event_key == "cluster-test" for ev in evidence)

    def test_determinism(self, sample_item):
        """Test that cartridge produces deterministic output."""
        cart1 = TextSubwordCartridge()
        cart2 = TextSubwordCartridge()

        ev1 = cart1.process_item(sample_item, "cluster")
        ev2 = cart2.process_item(sample_item, "cluster")

        # Same inputs should produce same outputs
        assert len(ev1) == len(ev2)
        for e1, e2 in zip(ev1, ev2):
            assert e1.to_dict() == e2.to_dict()


# -----------------------------------------------------------------------------
# DigitMotifCartridge Tests
# -----------------------------------------------------------------------------


class TestDigitMotifCartridge:
    """Tests for DigitMotifCartridge."""

    def test_descriptor(self, digit_cartridge):
        desc = digit_cartridge.descriptor()
        assert desc.domain_id == "digit.v1"
        assert desc.motif_kind == "digit"
        assert desc.alphabet == "0-9"

    def test_encode(self, digit_cartridge, digit_item):
        symbol = digit_cartridge.encode(digit_item)
        assert symbol.item_id == digit_item.id
        assert len(symbol.sequences) > 0

        # Should find digit sequences
        digits = [s.digits for s in symbol.sequences]
        assert "1984" in digits
        assert "2024" in digits
        assert "1776" in digits

    def test_extract_motifs(self, digit_cartridge, digit_item):
        symbol = digit_cartridge.encode(digit_item)
        motifs = digit_cartridge.extract_motifs(symbol)

        assert len(motifs) > 0

        # Check motif structure
        for m in motifs:
            assert m.domain_id == "digit.v1"
            assert m.motif_id.startswith("digit.v1:")

        # Significant patterns should be core
        motif_map = {m.motif_text: m for m in motifs}
        if "1984" in motif_map:
            assert motif_map["1984"].lane_hint == "core"
        if "666" in motif_map:
            assert motif_map["666"].lane_hint == "core"

    def test_emit_evidence(self, digit_cartridge, digit_item):
        symbol = digit_cartridge.encode(digit_item)
        motifs = digit_cartridge.extract_motifs(symbol)
        evidence = digit_cartridge.emit_evidence(digit_item, motifs, "cluster-002")

        assert len(evidence) > 0
        for ev in evidence:
            assert ev.domain_id == "digit.v1"
            assert ev.event_key == "cluster-002"

    def test_determinism(self, digit_item):
        """Test deterministic output."""
        cart1 = DigitMotifCartridge()
        cart2 = DigitMotifCartridge()

        ev1 = cart1.process_item(digit_item, "cluster")
        ev2 = cart2.process_item(digit_item, "cluster")

        assert len(ev1) == len(ev2)
        for e1, e2 in zip(ev1, ev2):
            assert e1.to_dict() == e2.to_dict()

    def test_digit_entropy(self, digit_cartridge):
        """Test digit entropy calculation."""
        # All same digits = 0 entropy
        assert digit_cartridge._digit_entropy("111") == 0.0

        # All different digits = high entropy
        entropy_10 = digit_cartridge._digit_entropy("0123456789")
        assert entropy_10 > 0.9

        # Mixed = moderate entropy
        entropy_mixed = digit_cartridge._digit_entropy("1122")
        assert 0.0 < entropy_mixed < 1.0


# -----------------------------------------------------------------------------
# Registry Tests
# -----------------------------------------------------------------------------


class TestDomainRegistry:
    """Tests for DomainRegistry."""

    def test_register_cartridge(self):
        registry = DomainRegistry()
        registry.register(TextSubwordCartridge, priority=0)

        assert "text.subword.v1" in registry.list_all()

    def test_register_duplicate_fails(self):
        registry = DomainRegistry()
        registry.register(TextSubwordCartridge)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(TextSubwordCartridge)

    def test_enable_disable(self):
        registry = DomainRegistry()
        registry.register(TextSubwordCartridge, enabled=True)

        assert registry.is_enabled("text.subword.v1")

        registry.disable("text.subword.v1")
        assert not registry.is_enabled("text.subword.v1")

        registry.enable("text.subword.v1")
        assert registry.is_enabled("text.subword.v1")

    def test_load_enabled(self):
        registry = DomainRegistry()
        registry.register(TextSubwordCartridge, enabled=True, priority=10)
        registry.register(DigitMotifCartridge, enabled=True, priority=0)

        cartridges = registry.load_enabled()
        assert len(cartridges) == 2

        # Lower priority first
        assert cartridges[0].domain_id() == "digit.v1"
        assert cartridges[1].domain_id() == "text.subword.v1"

    def test_registry_hash_determinism(self):
        reg1 = DomainRegistry()
        reg1.register(TextSubwordCartridge)
        reg1.register(DigitMotifCartridge)

        reg2 = DomainRegistry()
        reg2.register(DigitMotifCartridge)  # Different order
        reg2.register(TextSubwordCartridge)

        # Should produce same hash regardless of registration order
        assert reg1.registry_hash() == reg2.registry_hash()

    def test_descriptors(self):
        registry = DomainRegistry()
        registry.register(TextSubwordCartridge)
        registry.register(DigitMotifCartridge)

        descs = registry.descriptors()
        assert len(descs) == 2
        domain_ids = [d.domain_id for d in descs]
        assert "text.subword.v1" in domain_ids
        assert "digit.v1" in domain_ids

    def test_to_dict(self):
        registry = DomainRegistry()
        registry.register(TextSubwordCartridge)

        d = registry.to_dict()
        assert d["total_count"] == 1
        assert d["enabled_count"] == 1
        assert "registry_hash" in d


class TestDefaultRegistry:
    """Tests for default registry factory."""

    def test_get_default_registry(self):
        registry = get_default_registry()
        assert registry is not None

        # Should have built-in cartridges
        domain_ids = registry.list_all()
        assert "text.subword.v1" in domain_ids
        assert "digit.v1" in domain_ids

    def test_singleton_behavior(self):
        reg1 = get_default_registry()
        reg2 = get_default_registry()
        assert reg1 is reg2

    def test_reset(self):
        reg1 = get_default_registry()
        reset_default_registry()
        reg2 = get_default_registry()
        assert reg1 is not reg2


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------


class TestCartridgeIntegration:
    """Integration tests for cartridge system."""

    def test_multi_domain_pipeline(self, sample_item):
        """Test processing through multiple domains."""
        registry = get_default_registry()
        cartridges = registry.load_enabled()

        all_evidence: List[NormalizedEvidence] = []
        event_key = "integration-test"

        for cart in cartridges:
            evidence = cart.process_item(sample_item, event_key)
            all_evidence.extend(evidence)

        # Should have evidence from both domains
        domains = set(ev.domain_id for ev in all_evidence)
        assert "text.subword.v1" in domains
        # digit.v1 may or may not have evidence depending on item content

    def test_evidence_aggregation(self, sample_item):
        """Test that evidence can be aggregated across domains."""
        registry = get_default_registry()
        text_cart = registry.get("text.subword.v1")

        evidence = text_cart.process_item(sample_item, "agg-test")

        # Group by motif_id
        by_motif: dict = {}
        for ev in evidence:
            if ev.motif_id not in by_motif:
                by_motif[ev.motif_id] = []
            by_motif[ev.motif_id].append(ev)

        # Each motif should have at least one evidence row
        assert all(len(rows) >= 1 for rows in by_motif.values())

    def test_namespacing_isolation(self):
        """Test that domain namespacing prevents collisions."""
        text_cart = TextSubwordCartridge()
        digit_cart = DigitMotifCartridge()

        # Both cartridges might have a motif for "111" patterns
        # but their IDs should be namespaced differently
        text_id = text_cart.make_motif_id("test")
        digit_id = digit_cart.make_motif_id("test")

        assert text_id == "text.subword.v1:test"
        assert digit_id == "digit.v1:test"
        assert text_id != digit_id


# -----------------------------------------------------------------------------
# Factory Function Tests
# -----------------------------------------------------------------------------


class TestFactoryFunctions:
    """Tests for cartridge factory functions."""

    def test_create_text_subword_cartridge(self):
        cart = create_text_subword_cartridge(
            min_token_len=5,
            min_sub_len=4,
        )
        desc = cart.descriptor()
        assert "min_token_len>=5" in desc.constraints
        assert "min_sub_len>=4" in desc.constraints

    def test_create_digit_cartridge(self):
        cart = create_digit_cartridge(
            min_len=4,
            max_len=6,
            additional_patterns=frozenset(["9999"]),
        )
        desc = cart.descriptor()
        assert "min_len>=4" in desc.constraints
        assert "max_len<=6" in desc.constraints
