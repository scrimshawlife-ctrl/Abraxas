"""
Tests for EvidencePack.v0 and EvidenceItem.v0

Verifies:
- Deterministic hashing
- Validation invariants
- Semantic equality
- Field constraints
"""

import pytest

from abx_familiar.ir import (
    EvidenceItem,
    EvidencePack,
    SOURCE_TYPES,
    CONFIDENCE_CLASSES,
)


# -------------------------
# EvidenceItem Fixtures
# -------------------------

@pytest.fixture
def web_evidence():
    """A valid web-sourced EvidenceItem."""
    return EvidenceItem(
        evidence_id="EV-001",
        source_type="web",
        url="https://example.com/article",
        timestamp="2026-01-27T12:00:00Z",
        provenance_hash="abc123def456",
        confidence_class="high",
    )


@pytest.fixture
def file_evidence():
    """A valid file-sourced EvidenceItem."""
    return EvidenceItem(
        evidence_id="EV-002",
        source_type="file",
        path="/data/reports/report.pdf",
        confidence_class="medium",
    )


@pytest.fixture
def sensor_evidence():
    """A valid sensor-sourced EvidenceItem."""
    return EvidenceItem(
        evidence_id="EV-003",
        source_type="sensor",
        source_id="sensor-alpha-001",
        timestamp="2026-01-27T12:00:00Z",
        confidence_class="low",
    )


@pytest.fixture
def none_evidence():
    """A valid none-sourced EvidenceItem (placeholder)."""
    return EvidenceItem(
        evidence_id="EV-004",
        source_type="none",
        confidence_class="unknown",
        not_computable=True,
        missing_fields=["source_url"],
    )


# -------------------------
# EvidencePack Fixtures
# -------------------------

@pytest.fixture
def valid_pack(web_evidence, file_evidence):
    """A valid EvidencePack with multiple items."""
    return EvidencePack(
        pack_id="PACK-001",
        items=[web_evidence, file_evidence],
        collection_context={"query": "test search"},
    )


@pytest.fixture
def empty_pack():
    """An empty EvidencePack."""
    return EvidencePack(
        pack_id="PACK-002",
        items=[],
    )


# -------------------------
# EvidenceItem Validation Tests
# -------------------------

class TestEvidenceItemValidation:
    """Tests for EvidenceItem validation."""

    def test_valid_web_evidence(self, web_evidence):
        """Valid web evidence should pass validation."""
        web_evidence.validate()  # Should not raise

    def test_valid_file_evidence(self, file_evidence):
        """Valid file evidence should pass validation."""
        file_evidence.validate()  # Should not raise

    def test_valid_sensor_evidence(self, sensor_evidence):
        """Valid sensor evidence should pass validation."""
        sensor_evidence.validate()  # Should not raise

    def test_valid_none_evidence(self, none_evidence):
        """Valid none evidence should pass validation."""
        none_evidence.validate()  # Should not raise

    def test_invalid_source_type_raises(self):
        """Invalid source_type should raise ValueError."""
        item = EvidenceItem(
            evidence_id="EV-ERR",
            source_type="invalid_type",
            url="https://example.com",
        )
        with pytest.raises(ValueError, match="Invalid source_type"):
            item.validate()

    def test_invalid_confidence_class_raises(self):
        """Invalid confidence_class should raise ValueError."""
        item = EvidenceItem(
            evidence_id="EV-ERR",
            source_type="web",
            url="https://example.com",
            confidence_class="very_high",  # Invalid
        )
        with pytest.raises(ValueError, match="Invalid confidence_class"):
            item.validate()

    def test_none_source_with_url_raises(self):
        """source_type='none' with url should raise ValueError."""
        item = EvidenceItem(
            evidence_id="EV-ERR",
            source_type="none",
            url="https://should-not-be-here.com",
        )
        with pytest.raises(ValueError, match='source_type="none" requires'):
            item.validate()

    def test_none_source_with_path_raises(self):
        """source_type='none' with path should raise ValueError."""
        item = EvidenceItem(
            evidence_id="EV-ERR",
            source_type="none",
            path="/some/path",
        )
        with pytest.raises(ValueError, match='source_type="none" requires'):
            item.validate()

    def test_none_source_with_source_id_raises(self):
        """source_type='none' with source_id should raise ValueError."""
        item = EvidenceItem(
            evidence_id="EV-ERR",
            source_type="none",
            source_id="some-id",
        )
        with pytest.raises(ValueError, match='source_type="none" requires'):
            item.validate()

    def test_non_none_source_requires_locator(self):
        """Non-'none' source_type requires at least one locator."""
        item = EvidenceItem(
            evidence_id="EV-ERR",
            source_type="web",
            # No url, path, or source_id
        )
        with pytest.raises(ValueError, match="requires at least one locator"):
            item.validate()

    def test_not_computable_without_missing_fields_raises(self):
        """not_computable=True without missing_fields should raise."""
        item = EvidenceItem(
            evidence_id="EV-ERR",
            source_type="none",
            not_computable=True,
            missing_fields=[],  # Empty - violation
        )
        with pytest.raises(ValueError, match="missing_fields to be non-empty"):
            item.validate()

    def test_all_source_types_valid(self):
        """All defined SOURCE_TYPES should be valid."""
        for src_type in SOURCE_TYPES:
            if src_type == "none":
                item = EvidenceItem(
                    evidence_id="TEST",
                    source_type=src_type,
                )
            else:
                item = EvidenceItem(
                    evidence_id="TEST",
                    source_type=src_type,
                    url="https://example.com",  # Provide locator
                )
            item.validate()  # Should not raise

    def test_all_confidence_classes_valid(self):
        """All defined CONFIDENCE_CLASSES should be valid."""
        for conf_class in CONFIDENCE_CLASSES:
            item = EvidenceItem(
                evidence_id="TEST",
                source_type="web",
                url="https://example.com",
                confidence_class=conf_class,
            )
            item.validate()  # Should not raise

    def test_multiple_locators_allowed(self):
        """Multiple locators should be allowed (not enforced as exactly-one)."""
        item = EvidenceItem(
            evidence_id="EV-MULTI",
            source_type="file",
            url="https://example.com/file",  # Both url and path
            path="/local/copy/file",
        )
        item.validate()  # Should not raise


# -------------------------
# EvidenceItem Hashing Tests
# -------------------------

class TestEvidenceItemHashing:
    """Tests for EvidenceItem deterministic hashing."""

    def test_hash_is_deterministic(self, web_evidence):
        """Same item should produce same hash."""
        hash1 = web_evidence.hash()
        hash2 = web_evidence.hash()
        assert hash1 == hash2

    def test_hash_is_sha256(self, web_evidence):
        """Hash should be a valid SHA-256 hex string."""
        h = web_evidence.hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_equivalent_items_same_hash(self):
        """Two items with identical fields should have same hash."""
        item1 = EvidenceItem(
            evidence_id="EV-X",
            source_type="web",
            url="https://example.com",
            confidence_class="high",
        )
        item2 = EvidenceItem(
            evidence_id="EV-X",
            source_type="web",
            url="https://example.com",
            confidence_class="high",
        )
        assert item1.hash() == item2.hash()

    def test_different_evidence_id_different_hash(self, web_evidence):
        """Different evidence_id should produce different hash."""
        item2 = EvidenceItem(
            evidence_id="DIFFERENT-ID",
            source_type=web_evidence.source_type,
            url=web_evidence.url,
            timestamp=web_evidence.timestamp,
            provenance_hash=web_evidence.provenance_hash,
            confidence_class=web_evidence.confidence_class,
        )
        assert web_evidence.hash() != item2.hash()


# -------------------------
# EvidencePack Validation Tests
# -------------------------

class TestEvidencePackValidation:
    """Tests for EvidencePack validation."""

    def test_valid_pack_passes(self, valid_pack):
        """Valid pack should pass validation."""
        valid_pack.validate()  # Should not raise

    def test_empty_pack_passes(self, empty_pack):
        """Empty pack should pass validation."""
        empty_pack.validate()  # Should not raise

    def test_pack_validates_all_items(self):
        """Pack validation should validate all contained items."""
        invalid_item = EvidenceItem(
            evidence_id="EV-BAD",
            source_type="invalid_type",
            url="https://example.com",
        )
        pack = EvidencePack(
            pack_id="PACK-ERR",
            items=[invalid_item],
        )
        with pytest.raises(ValueError, match="Invalid source_type"):
            pack.validate()

    def test_pack_not_computable_without_missing_fields_raises(self):
        """not_computable=True without missing_fields should raise."""
        pack = EvidencePack(
            pack_id="PACK-ERR",
            items=[],
            not_computable=True,
            missing_fields=[],  # Empty - violation
        )
        with pytest.raises(ValueError, match="missing_fields to be non-empty"):
            pack.validate()

    def test_pack_items_must_be_evidence_items(self):
        """Pack items must be EvidenceItem objects."""
        pack = EvidencePack(
            pack_id="PACK-ERR",
            items=[{"evidence_id": "not-an-item"}],  # type: ignore
        )
        with pytest.raises(ValueError, match="must contain EvidenceItem"):
            pack.validate()


# -------------------------
# EvidencePack Hashing Tests
# -------------------------

class TestEvidencePackHashing:
    """Tests for EvidencePack deterministic hashing."""

    def test_hash_is_deterministic(self, valid_pack):
        """Same pack should produce same hash."""
        hash1 = valid_pack.hash()
        hash2 = valid_pack.hash()
        assert hash1 == hash2

    def test_hash_is_sha256(self, valid_pack):
        """Hash should be a valid SHA-256 hex string."""
        h = valid_pack.hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_equivalent_packs_same_hash(self, web_evidence):
        """Two packs with identical content should have same hash."""
        pack1 = EvidencePack(
            pack_id="PACK-X",
            items=[web_evidence],
            collection_context={"key": "value"},
        )
        # Create identical item (not same object reference)
        item_copy = EvidenceItem(
            evidence_id=web_evidence.evidence_id,
            source_type=web_evidence.source_type,
            url=web_evidence.url,
            timestamp=web_evidence.timestamp,
            provenance_hash=web_evidence.provenance_hash,
            confidence_class=web_evidence.confidence_class,
        )
        pack2 = EvidencePack(
            pack_id="PACK-X",
            items=[item_copy],
            collection_context={"key": "value"},
        )
        assert pack1.hash() == pack2.hash()

    def test_different_pack_id_different_hash(self, valid_pack, web_evidence, file_evidence):
        """Different pack_id should produce different hash."""
        pack2 = EvidencePack(
            pack_id="DIFFERENT-PACK-ID",
            items=[web_evidence, file_evidence],
            collection_context=valid_pack.collection_context,
        )
        assert valid_pack.hash() != pack2.hash()

    def test_item_order_matters(self, web_evidence, file_evidence):
        """Item order should affect hash."""
        pack1 = EvidencePack(
            pack_id="PACK",
            items=[web_evidence, file_evidence],
        )
        pack2 = EvidencePack(
            pack_id="PACK",
            items=[file_evidence, web_evidence],  # Reversed order
        )
        assert pack1.hash() != pack2.hash()

    def test_collection_context_order_irrelevant(self, web_evidence):
        """Collection context dict order should not affect hash."""
        pack1 = EvidencePack(
            pack_id="PACK",
            items=[web_evidence],
            collection_context={"z": 1, "a": 2},
        )
        pack2 = EvidencePack(
            pack_id="PACK",
            items=[web_evidence],
            collection_context={"a": 2, "z": 1},
        )
        assert pack1.hash() == pack2.hash()


# -------------------------
# EvidencePack Semantic Equality Tests
# -------------------------

class TestEvidencePackSemanticEquality:
    """Tests for semantic equality."""

    def test_identical_packs_semantically_equal(self, web_evidence):
        """Two packs with identical content should be semantically equal."""
        pack1 = EvidencePack(
            pack_id="PACK-X",
            items=[web_evidence],
        )
        item_copy = EvidenceItem(
            evidence_id=web_evidence.evidence_id,
            source_type=web_evidence.source_type,
            url=web_evidence.url,
            timestamp=web_evidence.timestamp,
            provenance_hash=web_evidence.provenance_hash,
            confidence_class=web_evidence.confidence_class,
        )
        pack2 = EvidencePack(
            pack_id="PACK-X",
            items=[item_copy],
        )
        assert pack1.semantically_equal(pack2)
        assert pack2.semantically_equal(pack1)

    def test_different_packs_not_semantically_equal(self, valid_pack, empty_pack):
        """Different packs should not be semantically equal."""
        assert not valid_pack.semantically_equal(empty_pack)

    def test_semantically_equal_with_non_pack_returns_false(self, valid_pack):
        """Comparing with non-pack should return False."""
        assert not valid_pack.semantically_equal("not a pack")
        assert not valid_pack.semantically_equal(None)
        assert not valid_pack.semantically_equal({"pack_id": "PACK-001"})


# -------------------------
# Payload Tests
# -------------------------

class TestPayload:
    """Tests for payload conversion."""

    def test_item_to_payload_returns_dict(self, web_evidence):
        """EvidenceItem.to_payload should return a dictionary."""
        payload = web_evidence.to_payload()
        assert isinstance(payload, dict)

    def test_item_payload_contains_all_fields(self, web_evidence):
        """Item payload should contain all fields."""
        payload = web_evidence.to_payload()
        expected_keys = {
            "evidence_id",
            "source_type",
            "url",
            "path",
            "source_id",
            "timestamp",
            "provenance_hash",
            "confidence_class",
            "meta",
            "not_computable",
            "missing_fields",
        }
        assert set(payload.keys()) == expected_keys

    def test_pack_to_payload_returns_dict(self, valid_pack):
        """EvidencePack.to_payload should return a dictionary."""
        payload = valid_pack.to_payload()
        assert isinstance(payload, dict)

    def test_pack_payload_contains_all_fields(self, valid_pack):
        """Pack payload should contain all fields."""
        payload = valid_pack.to_payload()
        expected_keys = {
            "pack_id",
            "items",
            "collection_context",
            "not_computable",
            "missing_fields",
        }
        assert set(payload.keys()) == expected_keys

    def test_pack_payload_items_are_dicts(self, valid_pack):
        """Pack payload items should be converted to dicts."""
        payload = valid_pack.to_payload()
        assert all(isinstance(item, dict) for item in payload["items"])


# -------------------------
# Edge Cases
# -------------------------

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_evidence_id_valid(self):
        """Empty evidence_id should be allowed."""
        item = EvidenceItem(
            evidence_id="",
            source_type="web",
            url="https://example.com",
        )
        item.validate()  # Should not raise

    def test_nested_meta(self):
        """Nested meta dict should hash correctly."""
        item = EvidenceItem(
            evidence_id="EV-NESTED",
            source_type="web",
            url="https://example.com",
            meta={
                "nested": {
                    "deep": {"value": 123}
                }
            },
        )
        h = item.hash()
        assert len(h) == 64

    def test_unicode_in_fields(self):
        """Unicode content should hash correctly."""
        item = EvidenceItem(
            evidence_id="EV-\u4e2d\u6587",  # Chinese characters
            source_type="web",
            url="https://example.com/\u00e9\u00e8",  # French accents
        )
        h = item.hash()
        assert len(h) == 64

    def test_special_json_values_in_meta(self):
        """Special JSON values should serialize correctly."""
        item = EvidenceItem(
            evidence_id="EV-SPECIAL",
            source_type="web",
            url="https://example.com",
            meta={
                "null_value": None,
                "bool_true": True,
                "bool_false": False,
                "float_value": 3.14159,
                "int_value": 42,
            },
        )
        h = item.hash()
        assert len(h) == 64

    def test_very_long_url(self):
        """Very long URL should hash correctly."""
        long_url = "https://example.com/" + "a" * 10000
        item = EvidenceItem(
            evidence_id="EV-LONG",
            source_type="web",
            url=long_url,
        )
        h = item.hash()
        assert len(h) == 64

    def test_pack_with_many_items(self):
        """Pack with many items should hash correctly."""
        items = [
            EvidenceItem(
                evidence_id=f"EV-{i}",
                source_type="web",
                url=f"https://example.com/{i}",
            )
            for i in range(100)
        ]
        pack = EvidencePack(
            pack_id="PACK-LARGE",
            items=items,
        )
        h = pack.hash()
        assert len(h) == 64
