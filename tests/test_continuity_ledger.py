"""
Tests for ContinuityLedgerEntry.v0

Verifies:
- Deterministic hashing
- Validation invariants
- Semantic equality
- Append-only record constraints
"""

import pytest

from abx_familiar.ir import ContinuityLedgerEntry


# -------------------------
# Fixtures
# -------------------------

@pytest.fixture
def complete_entry():
    """A complete ContinuityLedgerEntry with all fields."""
    return ContinuityLedgerEntry(
        run_id="RUN-001",
        input_hash="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        task_graph_hash="b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
        invocation_plan_hash="c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        output_hash="d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
        prior_run_id="RUN-000",
        delta_summary="Minor config changes",
        stabilization_cycle=3,
        meta={"environment": "production"},
    )


@pytest.fixture
def minimal_entry():
    """A minimal ContinuityLedgerEntry with required fields only."""
    return ContinuityLedgerEntry(
        run_id="RUN-002",
        input_hash="hash1",
        task_graph_hash="hash2",
    )


@pytest.fixture
def first_run_entry():
    """A ContinuityLedgerEntry for a first run (no prior)."""
    return ContinuityLedgerEntry(
        run_id="RUN-FIRST",
        input_hash="initial_input_hash",
        task_graph_hash="initial_graph_hash",
        prior_run_id=None,
        delta_summary=None,
        stabilization_cycle=0,
    )


@pytest.fixture
def halted_entry():
    """A ContinuityLedgerEntry for a halted run (no output)."""
    return ContinuityLedgerEntry(
        run_id="RUN-HALT",
        input_hash="halted_input",
        task_graph_hash="halted_graph",
        invocation_plan_hash="halted_plan",
        output_hash=None,  # No output - halted
        prior_run_id="RUN-PREV",
        delta_summary="Run halted due to timeout",
        stabilization_cycle=1,
    )


# -------------------------
# Validation Tests
# -------------------------

class TestValidation:
    """Tests for ContinuityLedgerEntry validation."""

    def test_valid_complete_entry(self, complete_entry):
        """Complete entry should pass validation."""
        complete_entry.validate()  # Should not raise

    def test_valid_minimal_entry(self, minimal_entry):
        """Minimal entry should pass validation."""
        minimal_entry.validate()  # Should not raise

    def test_valid_first_run_entry(self, first_run_entry):
        """First run entry should pass validation."""
        first_run_entry.validate()  # Should not raise

    def test_valid_halted_entry(self, halted_entry):
        """Halted entry should pass validation."""
        halted_entry.validate()  # Should not raise

    def test_empty_run_id_raises(self):
        """Empty run_id should raise ValueError."""
        entry = ContinuityLedgerEntry(
            run_id="",
            input_hash="hash1",
            task_graph_hash="hash2",
        )
        with pytest.raises(ValueError, match="run_id must be non-empty"):
            entry.validate()

    def test_empty_input_hash_raises(self):
        """Empty input_hash should raise ValueError."""
        entry = ContinuityLedgerEntry(
            run_id="RUN-001",
            input_hash="",
            task_graph_hash="hash2",
        )
        with pytest.raises(ValueError, match="input_hash must be non-empty"):
            entry.validate()

    def test_empty_task_graph_hash_raises(self):
        """Empty task_graph_hash should raise ValueError."""
        entry = ContinuityLedgerEntry(
            run_id="RUN-001",
            input_hash="hash1",
            task_graph_hash="",
        )
        with pytest.raises(ValueError, match="task_graph_hash must be non-empty"):
            entry.validate()

    def test_negative_stabilization_cycle_raises(self):
        """Negative stabilization_cycle should raise ValueError."""
        entry = ContinuityLedgerEntry(
            run_id="RUN-001",
            input_hash="hash1",
            task_graph_hash="hash2",
            stabilization_cycle=-1,
        )
        with pytest.raises(ValueError, match="stabilization_cycle must be non-negative"):
            entry.validate()

    def test_zero_stabilization_cycle_valid(self):
        """Zero stabilization_cycle should be valid."""
        entry = ContinuityLedgerEntry(
            run_id="RUN-001",
            input_hash="hash1",
            task_graph_hash="hash2",
            stabilization_cycle=0,
        )
        entry.validate()  # Should not raise

    def test_not_computable_without_missing_fields_raises(self):
        """not_computable=True without missing_fields should raise."""
        entry = ContinuityLedgerEntry(
            run_id="RUN-001",
            input_hash="hash1",
            task_graph_hash="hash2",
            not_computable=True,
            missing_fields=[],
        )
        with pytest.raises(ValueError, match="missing_fields to be non-empty"):
            entry.validate()

    def test_not_computable_with_missing_fields_valid(self):
        """not_computable=True with missing_fields should be valid."""
        entry = ContinuityLedgerEntry(
            run_id="RUN-001",
            input_hash="hash1",
            task_graph_hash="hash2",
            not_computable=True,
            missing_fields=["output_hash"],
        )
        entry.validate()  # Should not raise


# -------------------------
# Hashing Tests
# -------------------------

class TestHashing:
    """Tests for ContinuityLedgerEntry deterministic hashing."""

    def test_hash_is_deterministic(self, complete_entry):
        """Same entry should produce same hash."""
        hash1 = complete_entry.hash()
        hash2 = complete_entry.hash()
        assert hash1 == hash2

    def test_hash_is_sha256(self, complete_entry):
        """Hash should be a valid SHA-256 hex string."""
        h = complete_entry.hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_equivalent_entries_same_hash(self):
        """Two entries with identical fields should have same hash."""
        entry1 = ContinuityLedgerEntry(
            run_id="RUN-X",
            input_hash="input",
            task_graph_hash="graph",
            stabilization_cycle=5,
        )
        entry2 = ContinuityLedgerEntry(
            run_id="RUN-X",
            input_hash="input",
            task_graph_hash="graph",
            stabilization_cycle=5,
        )
        assert entry1.hash() == entry2.hash()

    def test_different_run_id_different_hash(self, complete_entry):
        """Different run_id should produce different hash."""
        entry2 = ContinuityLedgerEntry(
            run_id="DIFFERENT-RUN",
            input_hash=complete_entry.input_hash,
            task_graph_hash=complete_entry.task_graph_hash,
            invocation_plan_hash=complete_entry.invocation_plan_hash,
            output_hash=complete_entry.output_hash,
            prior_run_id=complete_entry.prior_run_id,
            delta_summary=complete_entry.delta_summary,
            stabilization_cycle=complete_entry.stabilization_cycle,
            meta=dict(complete_entry.meta),
        )
        assert complete_entry.hash() != entry2.hash()

    def test_different_stabilization_cycle_different_hash(self, minimal_entry):
        """Different stabilization_cycle should produce different hash."""
        entry2 = ContinuityLedgerEntry(
            run_id=minimal_entry.run_id,
            input_hash=minimal_entry.input_hash,
            task_graph_hash=minimal_entry.task_graph_hash,
            stabilization_cycle=10,
        )
        assert minimal_entry.hash() != entry2.hash()

    def test_meta_order_irrelevant_for_hash(self):
        """Meta dict order should not affect hash (canonical JSON sorting)."""
        entry1 = ContinuityLedgerEntry(
            run_id="RUN",
            input_hash="input",
            task_graph_hash="graph",
            meta={"z": 1, "a": 2, "m": 3},
        )
        entry2 = ContinuityLedgerEntry(
            run_id="RUN",
            input_hash="input",
            task_graph_hash="graph",
            meta={"a": 2, "m": 3, "z": 1},
        )
        assert entry1.hash() == entry2.hash()

    def test_none_vs_missing_optional_fields_same_hash(self):
        """Explicit None and missing optional fields should produce same hash."""
        entry1 = ContinuityLedgerEntry(
            run_id="RUN",
            input_hash="input",
            task_graph_hash="graph",
            invocation_plan_hash=None,
            output_hash=None,
            prior_run_id=None,
            delta_summary=None,
        )
        entry2 = ContinuityLedgerEntry(
            run_id="RUN",
            input_hash="input",
            task_graph_hash="graph",
            # Optional fields use defaults (None)
        )
        assert entry1.hash() == entry2.hash()


# -------------------------
# Semantic Equality Tests
# -------------------------

class TestSemanticEquality:
    """Tests for semantic equality."""

    def test_identical_entries_semantically_equal(self):
        """Two entries with identical content should be semantically equal."""
        entry1 = ContinuityLedgerEntry(
            run_id="RUN-X",
            input_hash="input",
            task_graph_hash="graph",
        )
        entry2 = ContinuityLedgerEntry(
            run_id="RUN-X",
            input_hash="input",
            task_graph_hash="graph",
        )
        assert entry1.semantically_equal(entry2)
        assert entry2.semantically_equal(entry1)

    def test_different_entries_not_semantically_equal(self, complete_entry, minimal_entry):
        """Different entries should not be semantically equal."""
        assert not complete_entry.semantically_equal(minimal_entry)

    def test_semantically_equal_with_non_entry_returns_false(self, complete_entry):
        """Comparing with non-entry should return False."""
        assert not complete_entry.semantically_equal("not an entry")
        assert not complete_entry.semantically_equal(None)
        assert not complete_entry.semantically_equal({"run_id": "RUN-001"})


# -------------------------
# Payload Tests
# -------------------------

class TestPayload:
    """Tests for payload conversion."""

    def test_to_payload_returns_dict(self, complete_entry):
        """to_payload should return a dictionary."""
        payload = complete_entry.to_payload()
        assert isinstance(payload, dict)

    def test_payload_contains_all_fields(self, complete_entry):
        """Payload should contain all fields."""
        payload = complete_entry.to_payload()
        expected_keys = {
            "run_id",
            "input_hash",
            "task_graph_hash",
            "invocation_plan_hash",
            "output_hash",
            "prior_run_id",
            "delta_summary",
            "stabilization_cycle",
            "meta",
            "not_computable",
            "missing_fields",
        }
        assert set(payload.keys()) == expected_keys

    def test_payload_values_match(self, complete_entry):
        """Payload values should match entry fields."""
        payload = complete_entry.to_payload()
        assert payload["run_id"] == complete_entry.run_id
        assert payload["input_hash"] == complete_entry.input_hash
        assert payload["task_graph_hash"] == complete_entry.task_graph_hash
        assert payload["invocation_plan_hash"] == complete_entry.invocation_plan_hash
        assert payload["output_hash"] == complete_entry.output_hash
        assert payload["prior_run_id"] == complete_entry.prior_run_id
        assert payload["delta_summary"] == complete_entry.delta_summary
        assert payload["stabilization_cycle"] == complete_entry.stabilization_cycle
        assert payload["meta"] == complete_entry.meta

    def test_payload_missing_fields_is_list(self, complete_entry):
        """Payload missing_fields should be a list."""
        payload = complete_entry.to_payload()
        assert isinstance(payload["missing_fields"], list)


# -------------------------
# Edge Cases
# -------------------------

class TestEdgeCases:
    """Tests for edge cases."""

    def test_large_stabilization_cycle(self):
        """Large stabilization_cycle should hash correctly."""
        entry = ContinuityLedgerEntry(
            run_id="RUN-LARGE",
            input_hash="input",
            task_graph_hash="graph",
            stabilization_cycle=999999,
        )
        h = entry.hash()
        assert len(h) == 64

    def test_unicode_in_fields(self):
        """Unicode content should hash correctly."""
        entry = ContinuityLedgerEntry(
            run_id="RUN-\u4e2d\u6587",  # Chinese characters
            input_hash="hash\u00e9",  # French accent
            task_graph_hash="graph\U0001f600",  # Emoji
            delta_summary="Changes with \u00e9\u00e8\u00ea",
        )
        h = entry.hash()
        assert len(h) == 64

    def test_nested_meta(self):
        """Nested meta dict should hash correctly."""
        entry = ContinuityLedgerEntry(
            run_id="RUN-NESTED",
            input_hash="input",
            task_graph_hash="graph",
            meta={
                "nested": {
                    "deep": {"value": 123}
                }
            },
        )
        h = entry.hash()
        assert len(h) == 64

    def test_special_json_values_in_meta(self):
        """Special JSON values should serialize correctly."""
        entry = ContinuityLedgerEntry(
            run_id="RUN-SPECIAL",
            input_hash="input",
            task_graph_hash="graph",
            meta={
                "null_value": None,
                "bool_true": True,
                "bool_false": False,
                "float_value": 3.14159,
                "int_value": 42,
            },
        )
        h = entry.hash()
        assert len(h) == 64

    def test_long_delta_summary(self):
        """Long delta_summary should hash correctly."""
        entry = ContinuityLedgerEntry(
            run_id="RUN-LONG",
            input_hash="input",
            task_graph_hash="graph",
            delta_summary="X" * 10000,
        )
        h = entry.hash()
        assert len(h) == 64

    def test_chain_of_runs(self):
        """Simulated chain of runs should each hash uniquely."""
        entries = []
        prior_id = None
        for i in range(5):
            entry = ContinuityLedgerEntry(
                run_id=f"RUN-{i:03d}",
                input_hash=f"input_{i}",
                task_graph_hash=f"graph_{i}",
                prior_run_id=prior_id,
                stabilization_cycle=i,
            )
            entries.append(entry)
            prior_id = entry.run_id

        # All hashes should be unique
        hashes = [e.hash() for e in entries]
        assert len(hashes) == len(set(hashes))

    def test_stabilization_progression(self):
        """Entries at different stabilization cycles should differ."""
        base_params = {
            "run_id": "RUN",
            "input_hash": "input",
            "task_graph_hash": "graph",
        }
        entries = [
            ContinuityLedgerEntry(**base_params, stabilization_cycle=i)
            for i in range(10)
        ]
        hashes = [e.hash() for e in entries]
        assert len(hashes) == len(set(hashes))
