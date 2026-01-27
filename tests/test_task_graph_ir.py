"""
Tests for TaskGraphIR.v0

Verifies:
- Deterministic hashing
- Validation invariants
- Semantic equality
- Field constraints
"""

import pytest

from abx_familiar.ir import TaskGraphIR, TIER_SCOPES, MODES


# -------------------------
# Fixtures
# -------------------------

@pytest.fixture
def valid_ir():
    """A valid TaskGraphIR instance."""
    return TaskGraphIR(
        task_id="TASK-001",
        tier_scope="Academic",
        mode="Oracle",
        requested_ops=["sco_analyze", "tau_compute"],
        constraints={"max_tokens": 1000, "domain": "music"},
        assumptions=["english_only"],
    )


@pytest.fixture
def minimal_ir():
    """A minimal valid TaskGraphIR instance."""
    return TaskGraphIR(
        task_id="TASK-002",
        tier_scope="Enterprise",
        mode="Analyst",
        requested_ops=[],
        constraints={},
    )


@pytest.fixture
def not_computable_ir():
    """A not-computable TaskGraphIR instance."""
    return TaskGraphIR(
        task_id="TASK-003",
        tier_scope="Psychonaut",
        mode="Ritual",
        requested_ops=["unknown_op"],
        constraints={},
        not_computable=True,
        missing_fields=["required_context"],
    )


# -------------------------
# Validation Tests
# -------------------------

class TestValidation:
    """Tests for TaskGraphIR validation."""

    def test_valid_ir_passes_validation(self, valid_ir):
        """Valid IR should pass validation without error."""
        valid_ir.validate()  # Should not raise

    def test_minimal_ir_passes_validation(self, minimal_ir):
        """Minimal IR should pass validation without error."""
        minimal_ir.validate()  # Should not raise

    def test_not_computable_ir_passes_validation(self, not_computable_ir):
        """Not-computable IR with missing_fields should pass validation."""
        not_computable_ir.validate()  # Should not raise

    def test_invalid_tier_scope_raises(self):
        """Invalid tier_scope should raise ValueError."""
        ir = TaskGraphIR(
            task_id="TASK-ERR",
            tier_scope="InvalidScope",
            mode="Oracle",
            requested_ops=[],
            constraints={},
        )
        with pytest.raises(ValueError, match="Invalid tier_scope"):
            ir.validate()

    def test_invalid_mode_raises(self):
        """Invalid mode should raise ValueError."""
        ir = TaskGraphIR(
            task_id="TASK-ERR",
            tier_scope="Academic",
            mode="InvalidMode",
            requested_ops=[],
            constraints={},
        )
        with pytest.raises(ValueError, match="Invalid mode"):
            ir.validate()

    def test_not_computable_without_missing_fields_raises(self):
        """not_computable=True without missing_fields should raise."""
        ir = TaskGraphIR(
            task_id="TASK-ERR",
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=[],
            constraints={},
            not_computable=True,
            missing_fields=[],  # Empty - violation
        )
        with pytest.raises(ValueError, match="missing_fields to be non-empty"):
            ir.validate()

    def test_all_tier_scopes_valid(self):
        """All defined TIER_SCOPES should be valid."""
        for scope in TIER_SCOPES:
            ir = TaskGraphIR(
                task_id="TEST",
                tier_scope=scope,
                mode="Oracle",
                requested_ops=[],
                constraints={},
            )
            ir.validate()  # Should not raise

    def test_all_modes_valid(self):
        """All defined MODES should be valid."""
        for mode in MODES:
            ir = TaskGraphIR(
                task_id="TEST",
                tier_scope="Academic",
                mode=mode,
                requested_ops=[],
                constraints={},
            )
            ir.validate()  # Should not raise


# -------------------------
# Hashing Tests
# -------------------------

class TestHashing:
    """Tests for deterministic hashing."""

    def test_hash_is_deterministic(self, valid_ir):
        """Same IR should produce same hash."""
        hash1 = valid_ir.hash()
        hash2 = valid_ir.hash()
        assert hash1 == hash2

    def test_hash_is_sha256(self, valid_ir):
        """Hash should be a valid SHA-256 hex string."""
        h = valid_ir.hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_equivalent_irs_same_hash(self):
        """Two IRs with identical fields should have same hash."""
        ir1 = TaskGraphIR(
            task_id="TASK-X",
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=["op1", "op2"],
            constraints={"a": 1, "b": 2},
        )
        ir2 = TaskGraphIR(
            task_id="TASK-X",
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=["op1", "op2"],
            constraints={"a": 1, "b": 2},
        )
        assert ir1.hash() == ir2.hash()

    def test_different_task_id_different_hash(self, valid_ir):
        """Different task_id should produce different hash."""
        ir2 = TaskGraphIR(
            task_id="DIFFERENT-ID",
            tier_scope=valid_ir.tier_scope,
            mode=valid_ir.mode,
            requested_ops=list(valid_ir.requested_ops),
            constraints=dict(valid_ir.constraints),
            assumptions=list(valid_ir.assumptions),
        )
        assert valid_ir.hash() != ir2.hash()

    def test_dict_order_irrelevant_for_constraints(self):
        """Constraint dict order should not affect hash (canonical JSON sorting)."""
        ir1 = TaskGraphIR(
            task_id="TASK",
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=[],
            constraints={"z": 1, "a": 2, "m": 3},
        )
        ir2 = TaskGraphIR(
            task_id="TASK",
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=[],
            constraints={"a": 2, "m": 3, "z": 1},
        )
        assert ir1.hash() == ir2.hash()

    def test_list_order_matters_for_requested_ops(self):
        """List order should affect hash (ops are ordered)."""
        ir1 = TaskGraphIR(
            task_id="TASK",
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=["op1", "op2"],
            constraints={},
        )
        ir2 = TaskGraphIR(
            task_id="TASK",
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=["op2", "op1"],
            constraints={},
        )
        assert ir1.hash() != ir2.hash()


# -------------------------
# Semantic Equality Tests
# -------------------------

class TestSemanticEquality:
    """Tests for semantic equality."""

    def test_identical_irs_semantically_equal(self):
        """Two IRs with identical content should be semantically equal."""
        ir1 = TaskGraphIR(
            task_id="TASK-X",
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=["op1"],
            constraints={"key": "value"},
        )
        ir2 = TaskGraphIR(
            task_id="TASK-X",
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=["op1"],
            constraints={"key": "value"},
        )
        assert ir1.semantically_equal(ir2)
        assert ir2.semantically_equal(ir1)

    def test_different_irs_not_semantically_equal(self, valid_ir, minimal_ir):
        """Different IRs should not be semantically equal."""
        assert not valid_ir.semantically_equal(minimal_ir)

    def test_semantically_equal_with_non_ir_returns_false(self, valid_ir):
        """Comparing with non-IR should return False."""
        assert not valid_ir.semantically_equal("not an IR")
        assert not valid_ir.semantically_equal(None)
        assert not valid_ir.semantically_equal({"task_id": "TASK-001"})


# -------------------------
# Payload Tests
# -------------------------

class TestPayload:
    """Tests for payload conversion."""

    def test_to_payload_returns_dict(self, valid_ir):
        """to_payload should return a dictionary."""
        payload = valid_ir.to_payload()
        assert isinstance(payload, dict)

    def test_payload_contains_all_fields(self, valid_ir):
        """Payload should contain all IR fields."""
        payload = valid_ir.to_payload()
        expected_keys = {
            "task_id",
            "tier_scope",
            "mode",
            "requested_ops",
            "constraints",
            "assumptions",
            "not_computable",
            "missing_fields",
        }
        assert set(payload.keys()) == expected_keys

    def test_payload_values_match_ir(self, valid_ir):
        """Payload values should match IR fields."""
        payload = valid_ir.to_payload()
        assert payload["task_id"] == valid_ir.task_id
        assert payload["tier_scope"] == valid_ir.tier_scope
        assert payload["mode"] == valid_ir.mode
        assert payload["requested_ops"] == list(valid_ir.requested_ops)
        assert payload["constraints"] == valid_ir.constraints
        assert payload["assumptions"] == list(valid_ir.assumptions)
        assert payload["not_computable"] == valid_ir.not_computable
        assert payload["missing_fields"] == list(valid_ir.missing_fields)

    def test_payload_creates_copies_of_lists(self, valid_ir):
        """Payload lists should be copies, not references."""
        payload = valid_ir.to_payload()
        # Modifying payload should not affect original
        payload["requested_ops"].append("new_op")
        assert "new_op" not in valid_ir.requested_ops


# -------------------------
# Immutability Tests
# -------------------------

class TestImmutability:
    """Tests for dataclass immutability."""

    def test_ir_is_frozen(self, valid_ir):
        """TaskGraphIR should be frozen (immutable)."""
        with pytest.raises(AttributeError):
            valid_ir.task_id = "NEW-ID"

    def test_ir_not_natively_hashable_due_to_mutable_fields(self, valid_ir):
        """Frozen dataclass with mutable fields (list, dict) is NOT natively hashable.

        Use the .hash() method for deterministic canonical hashing instead.
        """
        with pytest.raises(TypeError, match="unhashable type"):
            {valid_ir}  # Should fail - lists and dicts aren't hashable

        # But our canonical hash method works
        assert len(valid_ir.hash()) == 64


# -------------------------
# Edge Cases
# -------------------------

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_strings_valid(self):
        """Empty strings should be allowed (validation is schema-level only)."""
        ir = TaskGraphIR(
            task_id="",  # Empty task_id
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=[],
            constraints={},
        )
        ir.validate()  # Should not raise

    def test_nested_constraints(self):
        """Nested constraint dicts should hash correctly."""
        ir = TaskGraphIR(
            task_id="TASK",
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=[],
            constraints={
                "nested": {
                    "deep": {"value": 123}
                }
            },
        )
        h = ir.hash()
        assert len(h) == 64

    def test_unicode_in_fields(self):
        """Unicode content should hash correctly."""
        ir = TaskGraphIR(
            task_id="TASK-\u4e2d\u6587",  # Chinese characters
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=["\u00e9\u00e8\u00ea"],  # French accents
            constraints={"emoji": "\U0001f600"},  # Emoji
        )
        h = ir.hash()
        assert len(h) == 64

    def test_special_json_values(self):
        """Special JSON values should serialize correctly."""
        ir = TaskGraphIR(
            task_id="TASK",
            tier_scope="Academic",
            mode="Oracle",
            requested_ops=[],
            constraints={
                "null_value": None,
                "bool_true": True,
                "bool_false": False,
                "float_value": 3.14159,
                "int_value": 42,
            },
        )
        h = ir.hash()
        assert len(h) == 64
