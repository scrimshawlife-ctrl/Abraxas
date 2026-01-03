"""Universal Budget Vector (UBV) - Cross-module budget tracking.

Universal Tuning Plane v0.4 - Multi-subsystem budget measurement and enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from abraxas.tuning.budget_schema import BudgetDimension


MeasurementWindow = Literal["per_run", "per_day", "per_week"]


@dataclass(frozen=True)
class UniversalBudgetVector:
    """Universal Budget Vector - cross-module resource budgets.

    All budgets are bounded, deterministic measurements.
    """

    # Compute budgets
    cpu_ms: BudgetDimension

    # I/O budgets
    io_write_bytes: BudgetDimension
    io_read_bytes: BudgetDimension

    # Network budgets
    network_calls: BudgetDimension
    network_bytes: BudgetDimension

    # Latency budgets
    latency_p95_ms: BudgetDimension

    # Storage budgets
    storage_growth_bytes: BudgetDimension

    # Special budgets
    decodo_calls: BudgetDimension
    risk_score: BudgetDimension  # Proxy for determinism + drift failures

    # Measurement context
    measurement_window: MeasurementWindow

    # Provenance
    run_ids: list[str]
    ledger_hashes: list[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "cpu_ms": {
                "measured": self.cpu_ms.measured,
                "budget": self.cpu_ms.budget,
                "hard_limit": self.cpu_ms.hard_limit,
            },
            "io_write_bytes": {
                "measured": self.io_write_bytes.measured,
                "budget": self.io_write_bytes.budget,
                "hard_limit": self.io_write_bytes.hard_limit,
            },
            "io_read_bytes": {
                "measured": self.io_read_bytes.measured,
                "budget": self.io_read_bytes.budget,
                "hard_limit": self.io_read_bytes.hard_limit,
            },
            "network_calls": {
                "measured": self.network_calls.measured,
                "budget": self.network_calls.budget,
                "hard_limit": self.network_calls.hard_limit,
            },
            "network_bytes": {
                "measured": self.network_bytes.measured,
                "budget": self.network_bytes.budget,
                "hard_limit": self.network_bytes.hard_limit,
            },
            "latency_p95_ms": {
                "measured": self.latency_p95_ms.measured,
                "budget": self.latency_p95_ms.budget,
                "hard_limit": self.latency_p95_ms.hard_limit,
            },
            "storage_growth_bytes": {
                "measured": self.storage_growth_bytes.measured,
                "budget": self.storage_growth_bytes.budget,
                "hard_limit": self.storage_growth_bytes.hard_limit,
            },
            "decodo_calls": {
                "measured": self.decodo_calls.measured,
                "budget": self.decodo_calls.budget,
                "hard_limit": self.decodo_calls.hard_limit,
            },
            "risk_score": {
                "measured": self.risk_score.measured,
                "budget": self.risk_score.budget,
                "hard_limit": self.risk_score.hard_limit,
            },
            "measurement_window": self.measurement_window,
            "run_ids": self.run_ids,
            "ledger_hashes": self.ledger_hashes,
        }

    def budget_violations(self) -> list[str]:
        """Check for budget violations.

        Returns:
            List of violation messages (empty if all budgets satisfied)
        """
        violations = []

        dimensions = [
            ("cpu_ms", self.cpu_ms),
            ("io_write_bytes", self.io_write_bytes),
            ("io_read_bytes", self.io_read_bytes),
            ("network_calls", self.network_calls),
            ("network_bytes", self.network_bytes),
            ("latency_p95_ms", self.latency_p95_ms),
            ("storage_growth_bytes", self.storage_growth_bytes),
            ("decodo_calls", self.decodo_calls),
            ("risk_score", self.risk_score),
        ]

        for name, dim in dimensions:
            if dim.hard_limit is not None and dim.measured > dim.hard_limit:
                violations.append(
                    f"{name}: measured {dim.measured} exceeds hard limit {dim.hard_limit}"
                )
            elif dim.budget is not None and dim.measured > dim.budget:
                violations.append(
                    f"{name}: measured {dim.measured} exceeds budget {dim.budget}"
                )

        return violations
