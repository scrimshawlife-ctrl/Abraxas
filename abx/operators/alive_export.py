"""
ABX Operator: alive_export

Exports ALIVE field signature to various formats (JSON, CSV, PDF).
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, Literal

# ALIVEFieldSignature replaced by alive.parse_field_signature capability
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


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
        # Parse and validate signature via capability
        ctx = RuneInvocationContext(
            run_id="ALIVE_EXPORT",
            subsystem_id="abx.operators.alive_export",
            git_hash="unknown"
        )

        parse_result = invoke_capability(
            "alive.parse_field_signature",
            {"field_signature": field_signature},
            ctx=ctx,
            strict_execution=True
        )

        parsed_signature = parse_result["parsed_signature"]
        if parsed_signature is None:
            raise ValueError(f"Invalid field signature: {parse_result['parse_error']}")

        if format == "json":
            return self._export_json(parsed_signature)
        elif format == "csv":
            return self._export_csv(parsed_signature)
        elif format == "pdf":
            raise NotImplementedError(
                "PDF export requires an external renderer and is not implemented"
            )
        else:
            raise ValueError(f"Unknown export format: {format}")

    def _export_json(self, signature: Dict[str, Any]) -> str:
        """Export as JSON."""
        return json.dumps(signature, indent=2)

    def _export_csv(self, signature: Dict[str, Any]) -> str:
        """Export as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "metric_id",
                "metric_version",
                "axis",
                "value",
                "confidence",
                "timestamp",
            ]
        )

        for axis, metrics in (
            ("influence", signature.get("influence", [])),
            ("vitality", signature.get("vitality", [])),
            ("life_logistics", signature.get("lifeLogistics", [])),
        ):
            for metric in metrics:
                writer.writerow(
                    [
                        metric.get("metricId", ""),
                        metric.get("metricVersion", ""),
                        axis,
                        metric.get("value", ""),
                        metric.get("confidence", ""),
                        metric.get("timestamp", ""),
                    ]
                )

        return output.getvalue().rstrip("\r\n")

    def __call__(
        self,
        field_signature: Dict[str, Any],
        format: Literal["json", "csv", "pdf"] = "json",
    ) -> str:
        """Allow operator to be called as function."""
        return self.execute(field_signature, format)
