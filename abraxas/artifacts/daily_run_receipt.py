"""
Daily Run Receipt — Execution Summary with Rent Metrics

Generates a receipt summarizing what happened during a run, including:
- Timestamp and configuration
- Metrics computed
- Ledgers updated
- Rent enforcement metrics
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RentMetrics:
    """Rent-related metrics for a run."""

    count_manifests_by_kind: Dict[str, int] = field(default_factory=dict)
    declared_ledgers: List[str] = field(default_factory=list)
    declared_tests: int = 0
    last_backtest_pass_rate: Optional[float] = None
    last_delta_counts: Dict[str, int] = field(default_factory=dict)


@dataclass
class DailyRunReceipt:
    """Receipt summarizing a daily run."""

    timestamp: str
    run_id: str
    status: str  # "success" | "partial" | "failed"
    duration_seconds: float = 0.0
    metrics_computed: List[str] = field(default_factory=list)
    ledgers_updated: List[str] = field(default_factory=list)
    artifacts_generated: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # NEW: Rent enforcement metrics
    rent_metrics: Optional[RentMetrics] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def save(self, output_path: str):
        """Save receipt to file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write(self.to_json())


def create_rent_metrics_from_manifests(
    manifests: Dict[str, List[Dict[str, Any]]],
    backtest_pass_rate: Optional[float] = None,
    delta_counts: Optional[Dict[str, int]] = None,
) -> RentMetrics:
    """
    Create rent metrics section from loaded manifests.

    Args:
        manifests: Dictionary of manifests by kind
        backtest_pass_rate: Optional backtest pass rate
        delta_counts: Optional delta counts (new_terms, mw_shifts, etc.)

    Returns:
        RentMetrics instance
    """
    # Count manifests by kind
    count_by_kind = {
        "metric": len(manifests.get("metrics", [])),
        "operator": len(manifests.get("operators", [])),
        "artifact": len(manifests.get("artifacts", [])),
    }

    # Collect all declared ledgers
    all_ledgers = set()
    total_tests = 0

    for kind in ["metrics", "operators", "artifacts"]:
        for manifest in manifests.get(kind, []):
            # Collect ledgers
            ledgers = manifest.get("proof", {}).get("ledgers_touched", [])
            all_ledgers.update(ledgers)

            # Count tests
            tests = manifest.get("proof", {}).get("tests", [])
            total_tests += len(tests)

    return RentMetrics(
        count_manifests_by_kind=count_by_kind,
        declared_ledgers=sorted(list(all_ledgers)),
        declared_tests=total_tests,
        last_backtest_pass_rate=backtest_pass_rate,
        last_delta_counts=delta_counts or {},
    )


def generate_run_receipt(
    run_id: str,
    status: str,
    duration_seconds: float = 0.0,
    metrics_computed: Optional[List[str]] = None,
    ledgers_updated: Optional[List[str]] = None,
    artifacts_generated: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
    rent_metrics: Optional[RentMetrics] = None,
) -> DailyRunReceipt:
    """
    Generate a daily run receipt.

    Args:
        run_id: Unique run identifier
        status: Run status
        duration_seconds: Run duration
        metrics_computed: List of metric IDs computed
        ledgers_updated: List of ledger paths updated
        artifacts_generated: List of artifact paths generated
        errors: List of error messages
        warnings: List of warning messages
        rent_metrics: Optional rent metrics

    Returns:
        DailyRunReceipt instance
    """
    return DailyRunReceipt(
        timestamp=datetime.utcnow().isoformat(),
        run_id=run_id,
        status=status,
        duration_seconds=duration_seconds,
        metrics_computed=metrics_computed or [],
        ledgers_updated=ledgers_updated or [],
        artifacts_generated=artifacts_generated or [],
        errors=errors or [],
        warnings=warnings or [],
        rent_metrics=rent_metrics,
    )
