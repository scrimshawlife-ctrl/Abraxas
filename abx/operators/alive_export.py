"""
ABX Operator: alive_export

Exports ALIVE field signature to various formats (JSON, CSV, PDF).
"""

from __future__ import annotations

import json
from typing import Any, Dict, Literal

from abraxas.alive.models import ALIVEFieldSignature


class ALIVEExportOperator:
    """
    ALIVE export operator.

    Converts field signature to export formats.
    """

    def execute(
        self,
        field_signature: Dict[str, Any],
        format: Literal["json", "csv", "pdf"] = "json",
    ) -> str:
        """
        Export field signature.

        Args:
            field_signature: ALIVE field signature data
            format: Export format

        Returns:
            Exported data as string
        """
        # Parse signature
        signature = ALIVEFieldSignature(**field_signature)

        if format == "json":
            return self._export_json(signature)
        elif format == "csv":
            return self._export_csv(signature)
        elif format == "pdf":
            # TODO: Implement PDF export
            raise NotImplementedError("PDF export not yet implemented")
        else:
            raise ValueError(f"Unknown export format: {format}")

    def _export_json(self, signature: ALIVEFieldSignature) -> str:
        """Export as JSON."""
        return signature.model_dump_json(indent=2)

    def _export_csv(self, signature: ALIVEFieldSignature) -> str:
        """Export as CSV."""
        # TODO: Implement CSV export with proper formatting
        # For now, return a simple CSV representation
        lines = [
            "metric_id,metric_version,axis,value,confidence,timestamp",
        ]

        for metric in signature.influence:
            lines.append(
                f"{metric.metricId},{metric.metricVersion},influence,"
                f"{metric.value},{metric.confidence},{metric.timestamp}"
            )

        for metric in signature.vitality:
            lines.append(
                f"{metric.metricId},{metric.metricVersion},vitality,"
                f"{metric.value},{metric.confidence},{metric.timestamp}"
            )

        for metric in signature.lifeLogistics:
            lines.append(
                f"{metric.metricId},{metric.metricVersion},life_logistics,"
                f"{metric.value},{metric.confidence},{metric.timestamp}"
            )

        return "\n".join(lines)

    def __call__(
        self,
        field_signature: Dict[str, Any],
        format: Literal["json", "csv", "pdf"] = "json",
    ) -> str:
        """Allow operator to be called as function."""
        return self.execute(field_signature, format)
