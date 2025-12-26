"""Artifact Generators: Non-commodity outputs for operational intelligence.

Specialized output formats:
- Cascade Sheet
- Manipulation Surface Map
- Contamination Advisory
- Trust Drift Graph Data
- Oracle Delta Ledger
- Daily Run Receipt (with rent metrics)

All artifacts support JSON/Markdown formats and delta-only mode.
"""

from .daily_run_receipt import (
    DailyRunReceipt,
    RentMetrics,
    create_rent_metrics_from_manifests,
    generate_run_receipt,
)

__all__ = [
    "DailyRunReceipt",
    "RentMetrics",
    "create_rent_metrics_from_manifests",
    "generate_run_receipt",
]
