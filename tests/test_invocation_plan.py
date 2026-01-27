"""
Tests for InvocationPlan.v0 and related classes

Verifies:
- Deterministic hashing
- Validation invariants
- Semantic equality
- Dependency graph constraints
"""

import pytest

from abx_familiar.ir import (
    RuneInvocation,
    DependencyEdge,
    BudgetAllocation,
    InvocationPlan,
    DETERMINISM_CLASSES,
    SIDE_EFFECTS,
)


# -------------------------
# RuneInvocation Fixtures
# -------------------------

@pytest.fixture
def strict_invocation():
    """A strict determinism RuneInvocation."""
    return RuneInvocation(
        invocation_id="INV-001",
        rune_id="oracle.v2.run",
        input_contract_ref="TaskGraphIR.v0",
        params={"seed": 42, "domain": "music"},
        determinism="strict",
        side_effects="none",
        cost_class="M",
        estimated_duration_ms=5000,
    )


@pytest.fixture
def bounded_invocation():
    """A bounded determinism RuneInvocation."""
    return RuneInvocation(
        invocation_id="INV-002",
        rune_id="weather.generate",
        input_contract_ref="EvidencePack.v0",
        params={"region": "global"},
        determinism="bounded",
        side_effects="ledger_append",
    )


@pytest.fixture
def minimal_invocation():
    """A minimal RuneInvocation with defaults."""
    return RuneInvocation(
        invocation_id="INV-003",
        rune_id="simple.rune",
        input_contract_ref="TaskGraphIR.v0",
    )


# -------------------------
# DependencyEdge Fixtures
# -------------------------

@pytest.fixture
def valid_edge():
    """A valid DependencyEdge."""
    return DependencyEdge(
        before_invocation_id="INV-001",
        after_invocation_id="INV-002",
    )


# -------------------------
# BudgetAllocation Fixtures
# -------------------------

@pytest.fixture
def full_budget():
    """A BudgetAllocation with both fields set."""
    return BudgetAllocation(
        compute_budget=100.0,
        time_budget_ms=30000,
    )


@pytest.fixture
def empty_budget():
    """A BudgetAllocation with defaults (no limits)."""
    return BudgetAllocation()


# -------------------------
# InvocationPlan Fixtures
# -------------------------

@pytest.fixture
def valid_plan(strict_invocation, bounded_invocation, valid_edge, full_budget):
    """A valid InvocationPlan with invocations and dependencies."""
    return InvocationPlan(
        plan_id="PLAN-001",
        rune_invocations=[strict_invocation, bounded_invocation],
        dependency_edges=[valid_edge],
        budget_allocation=full_budget,
    )


@pytest.fixture
def empty_plan():
    """An empty InvocationPlan."""
    return InvocationPlan(
        plan_id="PLAN-002",
        rune_invocations=[],
        dependency_edges=[],
    )


# -------------------------
# RuneInvocation Validation Tests
# -------------------------

class TestRuneInvocationValidation:
    """Tests for RuneInvocation validation."""

    def test_valid_strict_invocation(self, strict_invocation):
        """Valid strict invocation should pass validation."""
        strict_invocation.validate()  # Should not raise

    def test_valid_bounded_invocation(self, bounded_invocation):
        """Valid bounded invocation should pass validation."""
        bounded_invocation.validate()  # Should not raise

    def test_valid_minimal_invocation(self, minimal_invocation):
        """Minimal invocation with defaults should pass validation."""
        minimal_invocation.validate()  # Should not raise

    def test_invalid_determinism_raises(self):
        """Invalid determinism should raise ValueError."""
        inv = RuneInvocation(
            invocation_id="INV-ERR",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            determinism="invalid_determinism",
        )
        with pytest.raises(ValueError, match="Invalid determinism"):
            inv.validate()

    def test_invalid_side_effects_raises(self):
        """Invalid side_effects should raise ValueError."""
        inv = RuneInvocation(
            invocation_id="INV-ERR",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            side_effects="invalid_effects",
        )
        with pytest.raises(ValueError, match="Invalid side_effects"):
            inv.validate()

    def test_negative_duration_raises(self):
        """Negative estimated_duration_ms should raise ValueError."""
        inv = RuneInvocation(
            invocation_id="INV-ERR",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            estimated_duration_ms=-100,
        )
        with pytest.raises(ValueError, match="non-negative"):
            inv.validate()

    def test_not_computable_without_missing_fields_raises(self):
        """not_computable=True without missing_fields should raise."""
        inv = RuneInvocation(
            invocation_id="INV-ERR",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            not_computable=True,
            missing_fields=[],
        )
        with pytest.raises(ValueError, match="missing_fields to be non-empty"):
            inv.validate()

    def test_all_determinism_classes_valid(self):
        """All defined DETERMINISM_CLASSES should be valid."""
        for det_class in DETERMINISM_CLASSES:
            inv = RuneInvocation(
                invocation_id="TEST",
                rune_id="test.rune",
                input_contract_ref="TaskGraphIR.v0",
                determinism=det_class,
            )
            inv.validate()  # Should not raise

    def test_all_side_effects_valid(self):
        """All defined SIDE_EFFECTS should be valid."""
        for effect in SIDE_EFFECTS:
            inv = RuneInvocation(
                invocation_id="TEST",
                rune_id="test.rune",
                input_contract_ref="TaskGraphIR.v0",
                side_effects=effect,
            )
            inv.validate()  # Should not raise

    def test_non_serializable_params_raises(self):
        """Non-JSON-serializable params should raise ValueError."""
        inv = RuneInvocation(
            invocation_id="INV-ERR",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            params={"func": lambda x: x},  # Not serializable
        )
        with pytest.raises(ValueError, match="JSON-serializable"):
            inv.validate()


# -------------------------
# RuneInvocation Hashing Tests
# -------------------------

class TestRuneInvocationHashing:
    """Tests for RuneInvocation deterministic hashing."""

    def test_hash_is_deterministic(self, strict_invocation):
        """Same invocation should produce same hash."""
        hash1 = strict_invocation.hash()
        hash2 = strict_invocation.hash()
        assert hash1 == hash2

    def test_hash_is_sha256(self, strict_invocation):
        """Hash should be a valid SHA-256 hex string."""
        h = strict_invocation.hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_equivalent_invocations_same_hash(self):
        """Two invocations with identical fields should have same hash."""
        inv1 = RuneInvocation(
            invocation_id="INV-X",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            params={"key": "value"},
        )
        inv2 = RuneInvocation(
            invocation_id="INV-X",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            params={"key": "value"},
        )
        assert inv1.hash() == inv2.hash()

    def test_different_invocation_id_different_hash(self, strict_invocation):
        """Different invocation_id should produce different hash."""
        inv2 = RuneInvocation(
            invocation_id="DIFFERENT-ID",
            rune_id=strict_invocation.rune_id,
            input_contract_ref=strict_invocation.input_contract_ref,
            params=dict(strict_invocation.params),
            determinism=strict_invocation.determinism,
            side_effects=strict_invocation.side_effects,
        )
        assert strict_invocation.hash() != inv2.hash()


# -------------------------
# DependencyEdge Validation Tests
# -------------------------

class TestDependencyEdgeValidation:
    """Tests for DependencyEdge validation."""

    def test_valid_edge(self, valid_edge):
        """Valid edge should pass validation."""
        valid_edge.validate()  # Should not raise

    def test_empty_before_id_raises(self):
        """Empty before_invocation_id should raise ValueError."""
        edge = DependencyEdge(
            before_invocation_id="",
            after_invocation_id="INV-002",
        )
        with pytest.raises(ValueError, match="non-empty"):
            edge.validate()

    def test_empty_after_id_raises(self):
        """Empty after_invocation_id should raise ValueError."""
        edge = DependencyEdge(
            before_invocation_id="INV-001",
            after_invocation_id="",
        )
        with pytest.raises(ValueError, match="non-empty"):
            edge.validate()

    def test_self_referential_edge_raises(self):
        """Self-referential edge should raise ValueError."""
        edge = DependencyEdge(
            before_invocation_id="INV-001",
            after_invocation_id="INV-001",
        )
        with pytest.raises(ValueError, match="self-referential"):
            edge.validate()


# -------------------------
# BudgetAllocation Validation Tests
# -------------------------

class TestBudgetAllocationValidation:
    """Tests for BudgetAllocation validation."""

    def test_valid_full_budget(self, full_budget):
        """Valid full budget should pass validation."""
        full_budget.validate()  # Should not raise

    def test_valid_empty_budget(self, empty_budget):
        """Empty budget (no limits) should pass validation."""
        empty_budget.validate()  # Should not raise

    def test_negative_compute_budget_raises(self):
        """Negative compute_budget should raise ValueError."""
        budget = BudgetAllocation(compute_budget=-10.0)
        with pytest.raises(ValueError, match="non-negative"):
            budget.validate()

    def test_negative_time_budget_raises(self):
        """Negative time_budget_ms should raise ValueError."""
        budget = BudgetAllocation(time_budget_ms=-1000)
        with pytest.raises(ValueError, match="non-negative"):
            budget.validate()

    def test_zero_budgets_valid(self):
        """Zero budgets should be valid."""
        budget = BudgetAllocation(compute_budget=0.0, time_budget_ms=0)
        budget.validate()  # Should not raise


# -------------------------
# InvocationPlan Validation Tests
# -------------------------

class TestInvocationPlanValidation:
    """Tests for InvocationPlan validation."""

    def test_valid_plan_passes(self, valid_plan):
        """Valid plan should pass validation."""
        valid_plan.validate()  # Should not raise

    def test_empty_plan_passes(self, empty_plan):
        """Empty plan should pass validation."""
        empty_plan.validate()  # Should not raise

    def test_plan_validates_all_invocations(self):
        """Plan validation should validate all contained invocations."""
        invalid_inv = RuneInvocation(
            invocation_id="INV-BAD",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            determinism="invalid",
        )
        plan = InvocationPlan(
            plan_id="PLAN-ERR",
            rune_invocations=[invalid_inv],
        )
        with pytest.raises(ValueError, match="Invalid determinism"):
            plan.validate()

    def test_duplicate_invocation_id_raises(self):
        """Duplicate invocation_ids should raise ValueError."""
        inv1 = RuneInvocation(
            invocation_id="INV-DUP",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
        )
        inv2 = RuneInvocation(
            invocation_id="INV-DUP",  # Duplicate
            rune_id="other.rune",
            input_contract_ref="TaskGraphIR.v0",
        )
        plan = InvocationPlan(
            plan_id="PLAN-ERR",
            rune_invocations=[inv1, inv2],
        )
        with pytest.raises(ValueError, match="Duplicate invocation_id"):
            plan.validate()

    def test_edge_before_id_not_found_raises(self):
        """DependencyEdge referencing non-existent before_id should raise."""
        inv = RuneInvocation(
            invocation_id="INV-001",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
        )
        edge = DependencyEdge(
            before_invocation_id="NONEXISTENT",
            after_invocation_id="INV-001",
        )
        plan = InvocationPlan(
            plan_id="PLAN-ERR",
            rune_invocations=[inv],
            dependency_edges=[edge],
        )
        with pytest.raises(ValueError, match="before id not found"):
            plan.validate()

    def test_edge_after_id_not_found_raises(self):
        """DependencyEdge referencing non-existent after_id should raise."""
        inv = RuneInvocation(
            invocation_id="INV-001",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
        )
        edge = DependencyEdge(
            before_invocation_id="INV-001",
            after_invocation_id="NONEXISTENT",
        )
        plan = InvocationPlan(
            plan_id="PLAN-ERR",
            rune_invocations=[inv],
            dependency_edges=[edge],
        )
        with pytest.raises(ValueError, match="after id not found"):
            plan.validate()

    def test_plan_not_computable_without_missing_fields_raises(self):
        """not_computable=True without missing_fields should raise."""
        plan = InvocationPlan(
            plan_id="PLAN-ERR",
            rune_invocations=[],
            not_computable=True,
            missing_fields=[],
        )
        with pytest.raises(ValueError, match="missing_fields to be non-empty"):
            plan.validate()

    def test_invocations_must_be_rune_invocation_objects(self):
        """Plan invocations must be RuneInvocation objects."""
        plan = InvocationPlan(
            plan_id="PLAN-ERR",
            rune_invocations=[{"invocation_id": "not-an-object"}],  # type: ignore
        )
        with pytest.raises(ValueError, match="RuneInvocation objects"):
            plan.validate()

    def test_edges_must_be_dependency_edge_objects(self):
        """Plan edges must be DependencyEdge objects."""
        inv = RuneInvocation(
            invocation_id="INV-001",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
        )
        plan = InvocationPlan(
            plan_id="PLAN-ERR",
            rune_invocations=[inv],
            dependency_edges=[{"before": "A", "after": "B"}],  # type: ignore
        )
        with pytest.raises(ValueError, match="DependencyEdge objects"):
            plan.validate()


# -------------------------
# InvocationPlan Hashing Tests
# -------------------------

class TestInvocationPlanHashing:
    """Tests for InvocationPlan deterministic hashing."""

    def test_hash_is_deterministic(self, valid_plan):
        """Same plan should produce same hash."""
        hash1 = valid_plan.hash()
        hash2 = valid_plan.hash()
        assert hash1 == hash2

    def test_hash_is_sha256(self, valid_plan):
        """Hash should be a valid SHA-256 hex string."""
        h = valid_plan.hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_equivalent_plans_same_hash(self, strict_invocation):
        """Two plans with identical content should have same hash."""
        plan1 = InvocationPlan(
            plan_id="PLAN-X",
            rune_invocations=[strict_invocation],
        )
        # Create identical invocation (not same object reference)
        inv_copy = RuneInvocation(
            invocation_id=strict_invocation.invocation_id,
            rune_id=strict_invocation.rune_id,
            input_contract_ref=strict_invocation.input_contract_ref,
            params=dict(strict_invocation.params),
            determinism=strict_invocation.determinism,
            side_effects=strict_invocation.side_effects,
            cost_class=strict_invocation.cost_class,
            estimated_duration_ms=strict_invocation.estimated_duration_ms,
        )
        plan2 = InvocationPlan(
            plan_id="PLAN-X",
            rune_invocations=[inv_copy],
        )
        assert plan1.hash() == plan2.hash()

    def test_different_plan_id_different_hash(self, valid_plan, strict_invocation, bounded_invocation, valid_edge, full_budget):
        """Different plan_id should produce different hash."""
        plan2 = InvocationPlan(
            plan_id="DIFFERENT-PLAN-ID",
            rune_invocations=[strict_invocation, bounded_invocation],
            dependency_edges=[valid_edge],
            budget_allocation=full_budget,
        )
        assert valid_plan.hash() != plan2.hash()

    def test_invocation_order_matters(self, strict_invocation, bounded_invocation):
        """Invocation order should affect hash."""
        plan1 = InvocationPlan(
            plan_id="PLAN",
            rune_invocations=[strict_invocation, bounded_invocation],
        )
        plan2 = InvocationPlan(
            plan_id="PLAN",
            rune_invocations=[bounded_invocation, strict_invocation],
        )
        assert plan1.hash() != plan2.hash()


# -------------------------
# InvocationPlan Semantic Equality Tests
# -------------------------

class TestInvocationPlanSemanticEquality:
    """Tests for semantic equality."""

    def test_identical_plans_semantically_equal(self, strict_invocation):
        """Two plans with identical content should be semantically equal."""
        plan1 = InvocationPlan(
            plan_id="PLAN-X",
            rune_invocations=[strict_invocation],
        )
        inv_copy = RuneInvocation(
            invocation_id=strict_invocation.invocation_id,
            rune_id=strict_invocation.rune_id,
            input_contract_ref=strict_invocation.input_contract_ref,
            params=dict(strict_invocation.params),
            determinism=strict_invocation.determinism,
            side_effects=strict_invocation.side_effects,
            cost_class=strict_invocation.cost_class,
            estimated_duration_ms=strict_invocation.estimated_duration_ms,
        )
        plan2 = InvocationPlan(
            plan_id="PLAN-X",
            rune_invocations=[inv_copy],
        )
        assert plan1.semantically_equal(plan2)
        assert plan2.semantically_equal(plan1)

    def test_different_plans_not_semantically_equal(self, valid_plan, empty_plan):
        """Different plans should not be semantically equal."""
        assert not valid_plan.semantically_equal(empty_plan)

    def test_semantically_equal_with_non_plan_returns_false(self, valid_plan):
        """Comparing with non-plan should return False."""
        assert not valid_plan.semantically_equal("not a plan")
        assert not valid_plan.semantically_equal(None)
        assert not valid_plan.semantically_equal({"plan_id": "PLAN-001"})


# -------------------------
# Payload Tests
# -------------------------

class TestPayload:
    """Tests for payload conversion."""

    def test_invocation_to_payload_returns_dict(self, strict_invocation):
        """RuneInvocation.to_payload should return a dictionary."""
        payload = strict_invocation.to_payload()
        assert isinstance(payload, dict)

    def test_invocation_payload_contains_all_fields(self, strict_invocation):
        """Invocation payload should contain all fields."""
        payload = strict_invocation.to_payload()
        expected_keys = {
            "invocation_id",
            "rune_id",
            "input_contract_ref",
            "params",
            "determinism",
            "side_effects",
            "cost_class",
            "estimated_duration_ms",
            "not_computable",
            "missing_fields",
        }
        assert set(payload.keys()) == expected_keys

    def test_edge_to_payload_returns_dict(self, valid_edge):
        """DependencyEdge.to_payload should return a dictionary."""
        payload = valid_edge.to_payload()
        assert isinstance(payload, dict)
        assert "before_invocation_id" in payload
        assert "after_invocation_id" in payload

    def test_budget_to_payload_returns_dict(self, full_budget):
        """BudgetAllocation.to_payload should return a dictionary."""
        payload = full_budget.to_payload()
        assert isinstance(payload, dict)
        assert "compute_budget" in payload
        assert "time_budget_ms" in payload

    def test_plan_to_payload_returns_dict(self, valid_plan):
        """InvocationPlan.to_payload should return a dictionary."""
        payload = valid_plan.to_payload()
        assert isinstance(payload, dict)

    def test_plan_payload_contains_all_fields(self, valid_plan):
        """Plan payload should contain all fields."""
        payload = valid_plan.to_payload()
        expected_keys = {
            "plan_id",
            "rune_invocations",
            "dependency_edges",
            "budget_allocation",
            "not_computable",
            "missing_fields",
        }
        assert set(payload.keys()) == expected_keys

    def test_plan_payload_nested_structures_are_dicts(self, valid_plan):
        """Plan payload nested structures should be dicts."""
        payload = valid_plan.to_payload()
        assert all(isinstance(inv, dict) for inv in payload["rune_invocations"])
        assert all(isinstance(edge, dict) for edge in payload["dependency_edges"])
        assert isinstance(payload["budget_allocation"], dict)


# -------------------------
# Edge Cases
# -------------------------

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_invocation_id_valid(self):
        """Empty invocation_id should be allowed (validation is semantic-level)."""
        inv = RuneInvocation(
            invocation_id="",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
        )
        inv.validate()  # Should not raise

    def test_nested_params(self):
        """Nested params dict should hash correctly."""
        inv = RuneInvocation(
            invocation_id="INV-NESTED",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            params={
                "nested": {
                    "deep": {"value": 123}
                }
            },
        )
        h = inv.hash()
        assert len(h) == 64

    def test_unicode_in_fields(self):
        """Unicode content should hash correctly."""
        inv = RuneInvocation(
            invocation_id="INV-\u4e2d\u6587",  # Chinese characters
            rune_id="test.\u00e9\u00e8",  # French accents
            input_contract_ref="TaskGraphIR.v0",
        )
        h = inv.hash()
        assert len(h) == 64

    def test_plan_with_many_invocations(self):
        """Plan with many invocations should hash correctly."""
        invocations = [
            RuneInvocation(
                invocation_id=f"INV-{i}",
                rune_id="test.rune",
                input_contract_ref="TaskGraphIR.v0",
            )
            for i in range(100)
        ]
        plan = InvocationPlan(
            plan_id="PLAN-LARGE",
            rune_invocations=invocations,
        )
        h = plan.hash()
        assert len(h) == 64

    def test_complex_dependency_graph(self):
        """Complex dependency graph should validate correctly."""
        invocations = [
            RuneInvocation(
                invocation_id=f"INV-{i}",
                rune_id="test.rune",
                input_contract_ref="TaskGraphIR.v0",
            )
            for i in range(5)
        ]
        # Create chain: 0 -> 1 -> 2 -> 3 -> 4
        edges = [
            DependencyEdge(
                before_invocation_id=f"INV-{i}",
                after_invocation_id=f"INV-{i+1}",
            )
            for i in range(4)
        ]
        plan = InvocationPlan(
            plan_id="PLAN-CHAIN",
            rune_invocations=invocations,
            dependency_edges=edges,
        )
        plan.validate()  # Should not raise
        assert len(plan.hash()) == 64

    def test_params_order_irrelevant_for_hash(self):
        """Params dict order should not affect hash (canonical JSON sorting)."""
        inv1 = RuneInvocation(
            invocation_id="INV",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            params={"z": 1, "a": 2, "m": 3},
        )
        inv2 = RuneInvocation(
            invocation_id="INV",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            params={"a": 2, "m": 3, "z": 1},
        )
        assert inv1.hash() == inv2.hash()

    def test_zero_duration_valid(self):
        """Zero duration should be valid."""
        inv = RuneInvocation(
            invocation_id="INV-ZERO",
            rune_id="test.rune",
            input_contract_ref="TaskGraphIR.v0",
            estimated_duration_ms=0,
        )
        inv.validate()  # Should not raise
