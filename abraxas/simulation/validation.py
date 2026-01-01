"""Startup Validation: Gate logic that prevents invalid simulations from running.

ENFORCEMENT-GRADE checks:
- No orphan metrics (metrics without rune bindings)
- No unbound variables (vars referenced but not defined)
- No invalid rune bindings (missing metrics/vars)
- Deterministic RNG pinned with seed
- All required fields present

Simulations with validation failures MUST NOT run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from abraxas.simulation.registries.metric_registry import MetricRegistry
from abraxas.simulation.registries.rune_registry import RuneRegistry
from abraxas.simulation.registries.simvar_registry import SimVarRegistry


@dataclass
class ValidationError:
    """Single validation error."""
    error_type: str
    severity: str  # "CRITICAL" or "WARNING"
    message: str
    context: Optional[dict] = None

    def __str__(self) -> str:
        ctx = f" | {self.context}" if self.context else ""
        return f"[{self.severity}] {self.error_type}: {self.message}{ctx}"


class SimulationValidator:
    """Validation gate for simulation configurations.

    CRITICAL errors block simulation execution.
    WARNINGS are logged but don't block.
    """

    def __init__(
        self,
        metric_registry: MetricRegistry,
        simvar_registry: SimVarRegistry,
        rune_registry: RuneRegistry,
        sim_seed: Optional[int] = None,
    ):
        self.metric_registry = metric_registry
        self.simvar_registry = simvar_registry
        self.rune_registry = rune_registry
        self.sim_seed = sim_seed
        self.errors: List[ValidationError] = []

    def validate_all(self) -> List[ValidationError]:
        """Run all validation checks.

        Returns:
            List of ValidationError objects. Empty if fully valid.
        """
        self.errors = []

        # CRITICAL: Sim seed required for determinism
        self._check_sim_seed()

        # CRITICAL: No orphan metrics
        self._check_orphan_metrics()

        # CRITICAL: No unbound variables
        self._check_unbound_variables()

        # CRITICAL: Rune coupling integrity
        self._check_rune_coupling()

        # CRITICAL: Variable class/type validity
        self._check_var_definitions()

        # WARNING: Circular metric dependencies
        self._check_circular_dependencies()

        return self.errors

    def has_critical_errors(self) -> bool:
        """Check if any critical errors exist."""
        return any(e.severity == "CRITICAL" for e in self.errors)

    def _check_sim_seed(self):
        """Ensure sim_seed is provided for deterministic execution."""
        if self.sim_seed is None:
            self.errors.append(
                ValidationError(
                    error_type="MISSING_SIM_SEED",
                    severity="CRITICAL",
                    message="sim_seed is required for deterministic execution",
                )
            )

    def _check_orphan_metrics(self):
        """Check for metrics without rune bindings."""
        orphans = self.metric_registry.find_orphans(self.rune_registry)

        for orphan_id in orphans:
            self.errors.append(
                ValidationError(
                    error_type="ORPHAN_METRIC",
                    severity="CRITICAL",
                    message=f"Metric {orphan_id} has no rune bindings",
                    context={"metric_id": orphan_id},
                )
            )

    def _check_unbound_variables(self):
        """Check for variables that are referenced but not defined."""
        all_runes = self.rune_registry.list_all()
        referenced_vars = set()

        for rune in all_runes:
            for target in rune.var_targets:
                referenced_vars.add(target.var_id)

        # Check if all referenced vars exist
        for var_id in referenced_vars:
            if not self.simvar_registry.get(var_id):
                self.errors.append(
                    ValidationError(
                        error_type="UNBOUND_VARIABLE",
                        severity="CRITICAL",
                        message=f"Variable {var_id} is referenced but not defined",
                        context={"var_id": var_id},
                    )
                )

    def _check_rune_coupling(self):
        """Validate all rune bindings against metric and variable registries."""
        coupling_errors = self.rune_registry.validate_coupling(
            self.metric_registry, self.simvar_registry
        )

        for error_msg in coupling_errors:
            self.errors.append(
                ValidationError(
                    error_type="INVALID_RUNE_COUPLING",
                    severity="CRITICAL",
                    message=error_msg,
                )
            )

    def _check_var_definitions(self):
        """Check variable class/type/bounds validity."""
        for var in self.simvar_registry.list_all():
            # Check bounds structure
            if var.var_type == "continuous":
                if "min" not in var.bounds or "max" not in var.bounds:
                    self.errors.append(
                        ValidationError(
                            error_type="INVALID_VAR_BOUNDS",
                            severity="CRITICAL",
                            message=f"Variable {var.var_id} (continuous) missing min/max bounds",
                            context={"var_id": var.var_id},
                        )
                    )

            elif var.var_type == "categorical":
                if "categories" not in var.bounds:
                    self.errors.append(
                        ValidationError(
                            error_type="INVALID_VAR_BOUNDS",
                            severity="CRITICAL",
                            message=f"Variable {var.var_id} (categorical) missing categories",
                            context={"var_id": var.var_id},
                        )
                    )

            # Check coupling capacity
            if var.coupling_capacity.get("max_runes", 0) < 1:
                self.errors.append(
                    ValidationError(
                        error_type="INVALID_COUPLING_CAPACITY",
                        severity="CRITICAL",
                        message=f"Variable {var.var_id} has max_runes < 1",
                        context={"var_id": var.var_id},
                    )
                )

    def _check_circular_dependencies(self):
        """Check for circular metric dependencies (WARNING only)."""
        # Build dependency graph
        dep_graph = {}
        for metric in self.metric_registry.list_all():
            dep_graph[metric.metric_id] = metric.dependencies

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(metric_id):
            visited.add(metric_id)
            rec_stack.add(metric_id)

            for dep in dep_graph.get(metric_id, []):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(metric_id)
            return False

        for metric_id in dep_graph:
            if metric_id not in visited:
                if has_cycle(metric_id):
                    self.errors.append(
                        ValidationError(
                            error_type="CIRCULAR_DEPENDENCY",
                            severity="WARNING",
                            message=f"Circular dependency detected involving {metric_id}",
                            context={"metric_id": metric_id},
                        )
                    )


def run_startup_gate(
    metric_registry: MetricRegistry,
    simvar_registry: SimVarRegistry,
    rune_registry: RuneRegistry,
    sim_seed: Optional[int],
) -> List[ValidationError]:
    """Run startup validation gate.

    Args:
        metric_registry: Metric registry
        simvar_registry: Variable registry
        rune_registry: Rune registry
        sim_seed: Simulation seed (required)

    Returns:
        List of validation errors. Empty if valid.

    Raises:
        RuntimeError: If critical errors found
    """
    validator = SimulationValidator(
        metric_registry, simvar_registry, rune_registry, sim_seed
    )

    errors = validator.validate_all()

    if validator.has_critical_errors():
        critical_errors = [e for e in errors if e.severity == "CRITICAL"]
        error_msgs = "\n".join(str(e) for e in critical_errors)
        raise RuntimeError(
            f"Simulation validation FAILED with {len(critical_errors)} critical errors:\n{error_msgs}"
        )

    return errors
