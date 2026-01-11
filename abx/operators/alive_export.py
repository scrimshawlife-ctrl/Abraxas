"""
ABX Operator: alive_export

Exports ALIVE field signature to various formats (JSON, CSV, PDF).
"""

from __future__ import annotations

import json
from typing import Any, Dict, Literal

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


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
        signature = self._normalize_signature(field_signature)

        if format == "json":
            return self._export_json(signature)
        elif format == "csv":
            return self._export_csv(signature)
        elif format == "pdf":
            # TODO: Implement PDF export
            raise NotImplementedError("PDF export not yet implemented")
        else:
            raise ValueError(f"Unknown export format: {format}")

    def _export_json(self, signature: Dict[str, Any]) -> str:
        """Export as JSON."""
        return json.dumps(signature, ensure_ascii=False, indent=2)

    def _export_csv(self, signature: Dict[str, Any]) -> str:
        """Export as CSV."""
        # TODO: Implement CSV export with proper formatting
        # For now, return a simple CSV representation
        lines = [
            "metric_id,metric_version,axis,value,confidence,timestamp",
        ]

        for metric in signature.get("influence", []) or []:
            lines.append(
                f"{metric.get('metricId')},{metric.get('metricVersion')},influence,"
                f"{metric.get('value')},{metric.get('confidence')},{metric.get('timestamp')}"
            )

        for metric in signature.get("vitality", []) or []:
            lines.append(
                f"{metric.get('metricId')},{metric.get('metricVersion')},vitality,"
                f"{metric.get('value')},{metric.get('confidence')},{metric.get('timestamp')}"
            )

        for metric in signature.get("lifeLogistics", []) or []:
            lines.append(
                f"{metric.get('metricId')},{metric.get('metricVersion')},life_logistics,"
                f"{metric.get('value')},{metric.get('confidence')},{metric.get('timestamp')}"
            )

        return "\n".join(lines)

    def _normalize_signature(self, field_signature: Dict[str, Any]) -> Dict[str, Any]:
        run_id = str(field_signature.get("analysisId") or field_signature.get("subjectId") or "alive_export")
        ctx = RuneInvocationContext(
            run_id=run_id,
            subsystem_id="abx.operators.alive_export",
            git_hash="unknown",
        )
        result = invoke_capability(
            "alive.models.serialize",
            {"field_signature": field_signature},
            ctx=ctx,
            strict_execution=True,
        )
        return result["field_signature"]

    def __call__(
        self,
        field_signature: Dict[str, Any],
        format: Literal["json", "csv", "pdf"] = "json",
    ) -> str:
        """Allow operator to be called as function."""
        return self.execute(field_signature, format)
