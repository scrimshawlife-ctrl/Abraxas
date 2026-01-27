"""
Tests for DeliveryPack.v0 and AttachmentRef.v0

Verifies:
- Deterministic hashing
- Validation invariants
- Semantic equality
- Final output constraints
"""

import pytest

from abx_familiar.ir import AttachmentRef, DeliveryPack
from abx_familiar.ir.delivery_pack_v0 import MODES, TIER_SCOPES


# -------------------------
# AttachmentRef Fixtures
# -------------------------

@pytest.fixture
def evidence_attachment():
    """An evidence attachment reference."""
    return AttachmentRef(
        kind="evidence",
        ref_id="ev_pack_abc123",
        meta={"source_count": 5},
    )


@pytest.fixture
def ward_report_attachment():
    """A ward report attachment reference."""
    return AttachmentRef(
        kind="ward_report",
        ref_id="ward_def456",
        meta={"violations": 2, "warnings": 3},
    )


@pytest.fixture
def trace_attachment():
    """An execution trace attachment reference."""
    return AttachmentRef(
        kind="execution_trace",
        ref_id="trace_ghi789",
    )


# -------------------------
# DeliveryPack Fixtures
# -------------------------

@pytest.fixture
def oracle_delivery(evidence_attachment, ward_report_attachment):
    """An Oracle mode delivery pack."""
    return DeliveryPack(
        delivery_id="DEL-001",
        mode="Oracle",
        tier_scope="Academic",
        rendered_output="The symbolic weather indicates rising compression...",
        attachments=[evidence_attachment, ward_report_attachment],
        provenance_manifest={
            "run_id": "RUN-001",
            "task_graph_hash": "abc123",
            "timestamp": "2026-01-27T12:00:00Z",
        },
    )


@pytest.fixture
def ritual_delivery():
    """A Ritual mode delivery pack."""
    return DeliveryPack(
        delivery_id="DEL-002",
        mode="Ritual",
        tier_scope="Psychonaut",
        rendered_output="The patterns reveal themselves in spiral form...",
        attachments=[],
        provenance_manifest={"run_id": "RUN-002"},
    )


@pytest.fixture
def analyst_delivery(trace_attachment):
    """An Analyst mode delivery pack."""
    return DeliveryPack(
        delivery_id="DEL-003",
        mode="Analyst",
        tier_scope="Enterprise",
        rendered_output="Analysis complete. Key findings:\n1. ...",
        attachments=[trace_attachment],
        provenance_manifest={
            "run_id": "RUN-003",
            "execution_time_ms": 1500,
        },
    )


@pytest.fixture
def minimal_delivery():
    """A minimal delivery pack."""
    return DeliveryPack(
        delivery_id="DEL-004",
        mode="Oracle",
        tier_scope="Academic",
        rendered_output="Minimal output.",
    )


# -------------------------
# AttachmentRef Validation Tests
# -------------------------

class TestAttachmentRefValidation:
    """Tests for AttachmentRef validation."""

    def test_valid_evidence_attachment(self, evidence_attachment):
        """Valid evidence attachment should pass validation."""
        evidence_attachment.validate()  # Should not raise

    def test_valid_ward_report_attachment(self, ward_report_attachment):
        """Valid ward report attachment should pass validation."""
        ward_report_attachment.validate()  # Should not raise

    def test_valid_trace_attachment(self, trace_attachment):
        """Valid trace attachment should pass validation."""
        trace_attachment.validate()  # Should not raise

    def test_empty_kind_raises(self):
        """Empty kind should raise ValueError."""
        att = AttachmentRef(
            kind="",
            ref_id="some_id",
        )
        with pytest.raises(ValueError, match="kind must be non-empty"):
            att.validate()

    def test_empty_ref_id_raises(self):
        """Empty ref_id should raise ValueError."""
        att = AttachmentRef(
            kind="evidence",
            ref_id="",
        )
        with pytest.raises(ValueError, match="ref_id must be non-empty"):
            att.validate()

    def test_custom_kind_valid(self):
        """Custom kind values should be valid (no enum restriction)."""
        att = AttachmentRef(
            kind="custom_artifact_type",
            ref_id="custom_123",
        )
        att.validate()  # Should not raise


# -------------------------
# AttachmentRef Payload Tests
# -------------------------

class TestAttachmentRefPayload:
    """Tests for AttachmentRef payload conversion."""

    def test_to_payload_returns_dict(self, evidence_attachment):
        """to_payload should return a dictionary."""
        payload = evidence_attachment.to_payload()
        assert isinstance(payload, dict)

    def test_payload_contains_all_fields(self, evidence_attachment):
        """Payload should contain all fields."""
        payload = evidence_attachment.to_payload()
        expected_keys = {"kind", "ref_id", "meta"}
        assert set(payload.keys()) == expected_keys

    def test_payload_values_match(self, evidence_attachment):
        """Payload values should match attachment fields."""
        payload = evidence_attachment.to_payload()
        assert payload["kind"] == evidence_attachment.kind
        assert payload["ref_id"] == evidence_attachment.ref_id
        assert payload["meta"] == evidence_attachment.meta


# -------------------------
# DeliveryPack Validation Tests
# -------------------------

class TestDeliveryPackValidation:
    """Tests for DeliveryPack validation."""

    def test_valid_oracle_delivery(self, oracle_delivery):
        """Oracle delivery should pass validation."""
        oracle_delivery.validate()  # Should not raise

    def test_valid_ritual_delivery(self, ritual_delivery):
        """Ritual delivery should pass validation."""
        ritual_delivery.validate()  # Should not raise

    def test_valid_analyst_delivery(self, analyst_delivery):
        """Analyst delivery should pass validation."""
        analyst_delivery.validate()  # Should not raise

    def test_valid_minimal_delivery(self, minimal_delivery):
        """Minimal delivery should pass validation."""
        minimal_delivery.validate()  # Should not raise

    def test_invalid_mode_raises(self):
        """Invalid mode should raise ValueError."""
        pack = DeliveryPack(
            delivery_id="DEL-ERR",
            mode="InvalidMode",
            tier_scope="Academic",
            rendered_output="Output",
        )
        with pytest.raises(ValueError, match="Invalid mode"):
            pack.validate()

    def test_invalid_tier_scope_raises(self):
        """Invalid tier_scope should raise ValueError."""
        pack = DeliveryPack(
            delivery_id="DEL-ERR",
            mode="Oracle",
            tier_scope="InvalidTier",
            rendered_output="Output",
        )
        with pytest.raises(ValueError, match="Invalid tier_scope"):
            pack.validate()

    def test_all_modes_valid(self):
        """All defined MODES should be valid."""
        for mode in MODES:
            pack = DeliveryPack(
                delivery_id="TEST",
                mode=mode,
                tier_scope="Academic",
                rendered_output="Test output",
            )
            pack.validate()  # Should not raise

    def test_all_tier_scopes_valid(self):
        """All defined TIER_SCOPES should be valid."""
        for tier in TIER_SCOPES:
            pack = DeliveryPack(
                delivery_id="TEST",
                mode="Oracle",
                tier_scope=tier,
                rendered_output="Test output",
            )
            pack.validate()  # Should not raise

    def test_attachments_must_be_attachment_refs(self):
        """Attachments must be AttachmentRef objects."""
        pack = DeliveryPack(
            delivery_id="DEL-ERR",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
            attachments=[{"kind": "not_an_object"}],  # type: ignore
        )
        with pytest.raises(ValueError, match="AttachmentRef objects"):
            pack.validate()

    def test_invalid_attachment_propagates(self):
        """Invalid attachment should cause validation to fail."""
        invalid_att = AttachmentRef(
            kind="",  # Invalid - empty
            ref_id="ref",
        )
        pack = DeliveryPack(
            delivery_id="DEL-ERR",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
            attachments=[invalid_att],
        )
        with pytest.raises(ValueError, match="kind must be non-empty"):
            pack.validate()

    def test_not_computable_without_missing_fields_raises(self):
        """not_computable=True without missing_fields should raise."""
        pack = DeliveryPack(
            delivery_id="DEL-ERR",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
            not_computable=True,
            missing_fields=[],
        )
        with pytest.raises(ValueError, match="missing_fields to be non-empty"):
            pack.validate()


# -------------------------
# DeliveryPack Hashing Tests
# -------------------------

class TestDeliveryPackHashing:
    """Tests for DeliveryPack deterministic hashing."""

    def test_hash_is_deterministic(self, oracle_delivery):
        """Same pack should produce same hash."""
        hash1 = oracle_delivery.hash()
        hash2 = oracle_delivery.hash()
        assert hash1 == hash2

    def test_hash_is_sha256(self, oracle_delivery):
        """Hash should be a valid SHA-256 hex string."""
        h = oracle_delivery.hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_equivalent_packs_same_hash(self, evidence_attachment):
        """Two packs with identical content should have same hash."""
        pack1 = DeliveryPack(
            delivery_id="DEL-X",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Same output",
            attachments=[evidence_attachment],
        )
        # Create identical attachment
        att_copy = AttachmentRef(
            kind=evidence_attachment.kind,
            ref_id=evidence_attachment.ref_id,
            meta=dict(evidence_attachment.meta),
        )
        pack2 = DeliveryPack(
            delivery_id="DEL-X",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Same output",
            attachments=[att_copy],
        )
        assert pack1.hash() == pack2.hash()

    def test_different_delivery_id_different_hash(self, oracle_delivery, evidence_attachment, ward_report_attachment):
        """Different delivery_id should produce different hash."""
        pack2 = DeliveryPack(
            delivery_id="DIFFERENT-ID",
            mode=oracle_delivery.mode,
            tier_scope=oracle_delivery.tier_scope,
            rendered_output=oracle_delivery.rendered_output,
            attachments=[evidence_attachment, ward_report_attachment],
            provenance_manifest=dict(oracle_delivery.provenance_manifest),
        )
        assert oracle_delivery.hash() != pack2.hash()

    def test_different_output_different_hash(self, minimal_delivery):
        """Different rendered_output should produce different hash."""
        pack2 = DeliveryPack(
            delivery_id=minimal_delivery.delivery_id,
            mode=minimal_delivery.mode,
            tier_scope=minimal_delivery.tier_scope,
            rendered_output="Different output text.",
        )
        assert minimal_delivery.hash() != pack2.hash()

    def test_attachment_order_matters(self, evidence_attachment, ward_report_attachment):
        """Attachment order should affect hash."""
        pack1 = DeliveryPack(
            delivery_id="DEL",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
            attachments=[evidence_attachment, ward_report_attachment],
        )
        pack2 = DeliveryPack(
            delivery_id="DEL",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
            attachments=[ward_report_attachment, evidence_attachment],
        )
        assert pack1.hash() != pack2.hash()

    def test_provenance_order_irrelevant_for_hash(self):
        """Provenance manifest dict order should not affect hash."""
        pack1 = DeliveryPack(
            delivery_id="DEL",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
            provenance_manifest={"z": 1, "a": 2},
        )
        pack2 = DeliveryPack(
            delivery_id="DEL",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
            provenance_manifest={"a": 2, "z": 1},
        )
        assert pack1.hash() == pack2.hash()


# -------------------------
# DeliveryPack Semantic Equality Tests
# -------------------------

class TestDeliveryPackSemanticEquality:
    """Tests for semantic equality."""

    def test_identical_packs_semantically_equal(self):
        """Two packs with identical content should be semantically equal."""
        pack1 = DeliveryPack(
            delivery_id="DEL-X",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
        )
        pack2 = DeliveryPack(
            delivery_id="DEL-X",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
        )
        assert pack1.semantically_equal(pack2)
        assert pack2.semantically_equal(pack1)

    def test_different_packs_not_semantically_equal(self, oracle_delivery, ritual_delivery):
        """Different packs should not be semantically equal."""
        assert not oracle_delivery.semantically_equal(ritual_delivery)

    def test_semantically_equal_with_non_pack_returns_false(self, oracle_delivery):
        """Comparing with non-pack should return False."""
        assert not oracle_delivery.semantically_equal("not a pack")
        assert not oracle_delivery.semantically_equal(None)
        assert not oracle_delivery.semantically_equal({"delivery_id": "DEL-001"})


# -------------------------
# Payload Tests
# -------------------------

class TestPayload:
    """Tests for payload conversion."""

    def test_pack_to_payload_returns_dict(self, oracle_delivery):
        """to_payload should return a dictionary."""
        payload = oracle_delivery.to_payload()
        assert isinstance(payload, dict)

    def test_payload_contains_all_fields(self, oracle_delivery):
        """Payload should contain all fields."""
        payload = oracle_delivery.to_payload()
        expected_keys = {
            "delivery_id",
            "mode",
            "tier_scope",
            "rendered_output",
            "attachments",
            "provenance_manifest",
            "not_computable",
            "missing_fields",
        }
        assert set(payload.keys()) == expected_keys

    def test_payload_attachments_are_dicts(self, oracle_delivery):
        """Payload attachments should be converted to dicts."""
        payload = oracle_delivery.to_payload()
        assert all(isinstance(a, dict) for a in payload["attachments"])

    def test_payload_values_match(self, oracle_delivery):
        """Payload values should match pack fields."""
        payload = oracle_delivery.to_payload()
        assert payload["delivery_id"] == oracle_delivery.delivery_id
        assert payload["mode"] == oracle_delivery.mode
        assert payload["tier_scope"] == oracle_delivery.tier_scope
        assert payload["rendered_output"] == oracle_delivery.rendered_output


# -------------------------
# Edge Cases
# -------------------------

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_delivery_id_valid(self):
        """Empty delivery_id should be allowed."""
        pack = DeliveryPack(
            delivery_id="",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
        )
        pack.validate()  # Should not raise

    def test_empty_rendered_output_valid(self):
        """Empty rendered_output should be allowed."""
        pack = DeliveryPack(
            delivery_id="DEL",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="",
        )
        pack.validate()  # Should not raise

    def test_many_attachments(self, evidence_attachment):
        """Pack with many attachments should hash correctly."""
        attachments = [
            AttachmentRef(
                kind=f"type_{i}",
                ref_id=f"ref_{i}",
            )
            for i in range(100)
        ]
        pack = DeliveryPack(
            delivery_id="DEL-LARGE",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Large pack output",
            attachments=attachments,
        )
        h = pack.hash()
        assert len(h) == 64

    def test_unicode_in_fields(self):
        """Unicode content should hash correctly."""
        pack = DeliveryPack(
            delivery_id="DEL-\u4e2d\u6587",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output with \u00e9\u00e8\u00ea and \U0001f600",
        )
        h = pack.hash()
        assert len(h) == 64

    def test_long_rendered_output(self):
        """Long rendered_output should hash correctly."""
        pack = DeliveryPack(
            delivery_id="DEL-LONG",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="X" * 100000,
        )
        h = pack.hash()
        assert len(h) == 64

    def test_nested_provenance_manifest(self):
        """Nested provenance manifest should hash correctly."""
        pack = DeliveryPack(
            delivery_id="DEL-NESTED",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
            provenance_manifest={
                "nested": {
                    "deep": {"value": 123}
                }
            },
        )
        h = pack.hash()
        assert len(h) == 64

    def test_special_json_values_in_provenance(self):
        """Special JSON values should serialize correctly."""
        pack = DeliveryPack(
            delivery_id="DEL-SPECIAL",
            mode="Oracle",
            tier_scope="Academic",
            rendered_output="Output",
            provenance_manifest={
                "null_value": None,
                "bool_true": True,
                "bool_false": False,
                "float_value": 3.14159,
                "int_value": 42,
            },
        )
        h = pack.hash()
        assert len(h) == 64

    def test_multiline_rendered_output(self):
        """Multiline rendered output should hash correctly."""
        pack = DeliveryPack(
            delivery_id="DEL-MULTI",
            mode="Analyst",
            tier_scope="Enterprise",
            rendered_output="""
            Analysis Report
            ===============

            1. Finding one
            2. Finding two
            3. Finding three

            Conclusion: Everything is fine.
            """,
        )
        h = pack.hash()
        assert len(h) == 64
