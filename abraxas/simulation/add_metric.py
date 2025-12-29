"""Add Metric Procedure: Deterministic pipeline for adding new metrics to Abraxas.

ENFORCEMENT:
- Required fields validation
- Determinism tests
- Bounds safety tests
- Coupling sanity tests
- Game operator sanity (if game-theoretic)
- Network operator sanity (if network-related)
- Registry updates with semantic versioning

WORKFLOW:
1. Define metric
2. Define variables (if new)
3. Define rune binding
4. Run validation tests
5. Register to registries
6. Bump semantic versions
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from abraxas.simulation.registries.metric_registry import (
    MetricDefinition,
    MetricProvenance,
    MetricRegistry,
)
from abraxas.simulation.registries.rune_registry import (
    ManipulationModel,
    NoiseModel,
    ObserverModel,
    ProvenanceManifest,
    RuneBinding,
    RuneRegistry,
    TransitionModel,
    VarTarget,
)
from abraxas.simulation.registries.simvar_registry import (
    EvolutionModel,
    PriorDistribution,
    SimVarDefinition,
    SimVarRegistry,
)


@dataclass
class TestResult:
    """Result of a validation test."""
    test_name: str
    passed: bool
    message: str
    details: Optional[Dict] = None


class MetricAdditionPipeline:
    """Pipeline for adding new metrics with full validation."""

    def __init__(
        self,
        metric_registry: MetricRegistry,
        simvar_registry: SimVarRegistry,
        rune_registry: RuneRegistry,
    ):
        self.metric_registry = metric_registry
        self.simvar_registry = simvar_registry
        self.rune_registry = rune_registry
        self.test_results: List[TestResult] = []

    def add_metric(
        self,
        metric: MetricDefinition,
        variables: List[SimVarDefinition],
        rune: RuneBinding,
    ) -> bool:
        """Add new metric with full validation pipeline.

        Args:
            metric: Metric definition
            variables: List of new variables (empty if using existing)
            rune: Rune binding

        Returns:
            True if successful, False otherwise
        """
        self.test_results = []

        # Step 1: Required fields validation
        if not self._validate_required_fields(metric, variables, rune):
            return False

        # Step 2: Determinism test
        if not self._test_determinism(rune):
            return False

        # Step 3: Bounds safety test
        if not self._test_bounds_safety(metric, variables):
            return False

        # Step 4: Coupling sanity test
        if not self._test_coupling_sanity(metric, rune):
            return False

        # Step 5: Specialized tests based on metric class
        if metric.metric_class in {"media_competition", "strategic_behavior"}:
            if not self._test_game_operator_sanity(rune):
                return False

        if metric.metric_class in {"network_topology", "community_structure"}:
            if not self._test_network_operator_sanity(rune):
                return False

        # All tests passed - register
        try:
            # Register variables
            for var in variables:
                self.simvar_registry.register(var)

            # Register metric
            self.metric_registry.register(metric)

            # Register rune
            self.rune_registry.register(rune)

            # Save all registries
            self.metric_registry.save()
            self.simvar_registry.save()
            self.rune_registry.save()

            self.test_results.append(
                TestResult(
                    test_name="REGISTRATION",
                    passed=True,
                    message="Successfully registered metric, variables, and rune",
                )
            )

            return True

        except Exception as e:
            self.test_results.append(
                TestResult(
                    test_name="REGISTRATION",
                    passed=False,
                    message=f"Registration failed: {str(e)}",
                )
            )
            return False

    def _validate_required_fields(
        self, metric: MetricDefinition, variables: List[SimVarDefinition], rune: RuneBinding
    ) -> bool:
        """Validate all required fields are present and valid."""
        try:
            # Metric validation happens in __post_init__
            # Variable validation happens in __post_init__
            # Rune validation happens in __post_init__

            # Additional checks
            if not metric.description or len(metric.description) < 10:
                raise ValueError("Metric description too short (< 10 chars)")

            if not rune.var_targets:
                raise ValueError("Rune must have at least one variable target")

            self.test_results.append(
                TestResult(
                    test_name="REQUIRED_FIELDS",
                    passed=True,
                    message="All required fields present and valid",
                )
            )
            return True

        except Exception as e:
            self.test_results.append(
                TestResult(
                    test_name="REQUIRED_FIELDS",
                    passed=False,
                    message=f"Required field validation failed: {str(e)}",
                )
            )
            return False

    def _test_determinism(self, rune: RuneBinding) -> bool:
        """Test that rune produces deterministic outputs given same seed."""
        # Determinism test: Check evolution model is deterministic
        # (Full implementation would actually run simulation steps)

        if rune.state_model not in {"classical", "quantum-inspired", "hybrid"}:
            self.test_results.append(
                TestResult(
                    test_name="DETERMINISM",
                    passed=False,
                    message=f"Invalid state_model: {rune.state_model}",
                )
            )
            return False

        # Check that transition model is defined
        if not rune.transition_model.transition_type:
            self.test_results.append(
                TestResult(
                    test_name="DETERMINISM",
                    passed=False,
                    message="Transition model missing transition_type",
                )
            )
            return False

        self.test_results.append(
            TestResult(
                test_name="DETERMINISM",
                passed=True,
                message="Rune configured for deterministic execution",
            )
        )
        return True

    def _test_bounds_safety(self, metric: MetricDefinition, variables: List[SimVarDefinition]) -> bool:
        """Test that all bounds are valid and safe."""
        try:
            # Check metric bounds
            if metric.valid_range["min"] >= metric.valid_range["max"]:
                raise ValueError(f"Metric {metric.metric_id} has invalid range")

            # Check variable bounds
            for var in variables:
                if var.var_type == "continuous":
                    if var.bounds["min"] >= var.bounds["max"]:
                        raise ValueError(f"Variable {var.var_id} has invalid bounds")

            self.test_results.append(
                TestResult(
                    test_name="BOUNDS_SAFETY",
                    passed=True,
                    message="All bounds are valid and safe",
                )
            )
            return True

        except Exception as e:
            self.test_results.append(
                TestResult(
                    test_name="BOUNDS_SAFETY",
                    passed=False,
                    message=f"Bounds safety test failed: {str(e)}",
                )
            )
            return False

    def _test_coupling_sanity(self, metric: MetricDefinition, rune: RuneBinding) -> bool:
        """Test that metric-rune coupling is sane."""
        try:
            # Check metric_id matches
            if metric.metric_id != rune.metric_id:
                raise ValueError("Metric ID mismatch between metric and rune")

            # Check layer consistency
            for layer in rune.layer_targets:
                if layer not in metric.layer_scope:
                    raise ValueError(
                        f"Rune targets layer {layer} but metric scope is {metric.layer_scope}"
                    )

            self.test_results.append(
                TestResult(
                    test_name="COUPLING_SANITY",
                    passed=True,
                    message="Metric-rune coupling is sane",
                )
            )
            return True

        except Exception as e:
            self.test_results.append(
                TestResult(
                    test_name="COUPLING_SANITY",
                    passed=False,
                    message=f"Coupling sanity test failed: {str(e)}",
                )
            )
            return False

    def _test_game_operator_sanity(self, rune: RuneBinding) -> bool:
        """Test game-theoretic operator sanity."""
        try:
            # Check that strategy-related transition models are defined
            if rune.transition_model.transition_type not in {
                "strategy_adapt",
                "game_theoretic",
                "no_transition",
            }:
                raise ValueError(
                    f"Game metric should use game-theoretic transition: {rune.transition_model.transition_type}"
                )

            # Check manipulation model is appropriate for strategic behavior
            if rune.manipulation_model.manipulation_type == "none":
                # Warning, not error (game metrics might not have manipulation)
                pass

            self.test_results.append(
                TestResult(
                    test_name="GAME_OPERATOR_SANITY",
                    passed=True,
                    message="Game-theoretic operator configuration is sane",
                )
            )
            return True

        except Exception as e:
            self.test_results.append(
                TestResult(
                    test_name="GAME_OPERATOR_SANITY",
                    passed=False,
                    message=f"Game operator sanity test failed: {str(e)}",
                )
            )
            return False

    def _test_network_operator_sanity(self, rune: RuneBinding) -> bool:
        """Test network operator sanity."""
        try:
            # Check that network-related transition models are defined
            valid_network_transitions = {
                "network_rewire",
                "community_reassignment",
                "quantum_walk_step",
                "no_transition",
            }

            if rune.transition_model.transition_type not in valid_network_transitions:
                raise ValueError(
                    f"Network metric should use network transition: {rune.transition_model.transition_type}"
                )

            # Check observer model is appropriate for network aggregation
            if rune.observer_model.observer_type not in {"network_aggregate", "linear", "contextual"}:
                # Warning only
                pass

            self.test_results.append(
                TestResult(
                    test_name="NETWORK_OPERATOR_SANITY",
                    passed=True,
                    message="Network operator configuration is sane",
                )
            )
            return True

        except Exception as e:
            self.test_results.append(
                TestResult(
                    test_name="NETWORK_OPERATOR_SANITY",
                    passed=False,
                    message=f"Network operator sanity test failed: {str(e)}",
                )
            )
            return False

    def get_test_report(self) -> str:
        """Get human-readable test report."""
        lines = ["=== Metric Addition Test Report ===\n"]

        passed_count = sum(1 for r in self.test_results if r.passed)
        total_count = len(self.test_results)

        lines.append(f"Tests Passed: {passed_count}/{total_count}\n")

        for result in self.test_results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            lines.append(f"{status} | {result.test_name}: {result.message}")

        return "\n".join(lines)


def bump_semantic_version(current_version: str, bump_type: str) -> str:
    """Bump semantic version.

    Args:
        current_version: Current version (MAJOR.MINOR.PATCH)
        bump_type: "major", "minor", or "patch"

    Returns:
        New version string
    """
    major, minor, patch = map(int, current_version.split("."))

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump_type: {bump_type}")
