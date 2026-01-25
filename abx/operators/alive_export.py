"""
ABX Operator: alive_export

Exports ALIVE field signature to various formats (JSON, CSV, PDF).
"""

from __future__ import annotations

import json
import csv
import io
from datetime import datetime
from typing import Any, Dict, Iterable, Literal

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
            return self._export_pdf(signature)
        else:
            raise ValueError(f"Unknown export format: {format}")

    def _export_json(self, signature: Dict[str, Any]) -> str:
        """Export as JSON."""
        return json.dumps(signature, ensure_ascii=False, indent=2)

    def _export_csv(self, signature: Dict[str, Any]) -> str:
        """Export as CSV."""
        output = io.StringIO()
        fieldnames = [
            "analysis_id",
            "subject_id",
            "axis",
            "metric_id",
            "metric_version",
            "status",
            "value",
            "confidence",
            "timestamp",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()

        analysis_id = signature.get("analysisId")
        subject_id = signature.get("subjectId")

        def _serialize_timestamp(value: Any) -> str:
            if isinstance(value, datetime):
                return value.isoformat()
            if value is None:
                return ""
            return str(value)

        def _iter_metrics(axis: str, metrics: Iterable[Dict[str, Any]]) -> None:
            for metric in metrics:
                writer.writerow(
                    {
                        "analysis_id": analysis_id,
                        "subject_id": subject_id,
                        "axis": axis,
                        "metric_id": metric.get("metricId"),
                        "metric_version": metric.get("metricVersion"),
                        "status": metric.get("status"),
                        "value": metric.get("value"),
                        "confidence": metric.get("confidence"),
                        "timestamp": _serialize_timestamp(metric.get("timestamp")),
                    }
                )

        _iter_metrics("influence", signature.get("influence", []) or [])
        _iter_metrics("vitality", signature.get("vitality", []) or [])
        _iter_metrics("life_logistics", signature.get("lifeLogistics", []) or [])

        return output.getvalue().rstrip("\n")

    def _export_pdf(self, signature: Dict[str, Any]) -> str:
        """Export as PDF."""
        lines = self._format_pdf_lines(signature)
        pdf_bytes = self._render_pdf(lines)
        return pdf_bytes.decode("latin-1")

    def _format_pdf_lines(self, signature: Dict[str, Any]) -> list[str]:
        composite = signature.get("compositeScore", {}) or {}
        lines = [
            "ALIVE Field Signature",
            f"Analysis ID: {signature.get('analysisId')}",
            f"Subject ID: {signature.get('subjectId')}",
            f"Timestamp: {signature.get('timestamp')}",
            f"Composite Score: {composite.get('overall')}",
            "",
            "Influence Metrics:",
        ]

        def _append_metrics(axis: str, metrics: Iterable[Dict[str, Any]]) -> None:
            if not metrics:
                lines.append("  (none)")
                return
            for metric in metrics:
                lines.append(
                    "  - {metric_id} v{version} [{status}] value={value} "
                    "confidence={confidence} ts={timestamp}".format(
                        metric_id=metric.get("metricId"),
                        version=metric.get("metricVersion"),
                        status=metric.get("status"),
                        value=metric.get("value"),
                        confidence=metric.get("confidence"),
                        timestamp=metric.get("timestamp"),
                    )
                )

        _append_metrics("influence", signature.get("influence", []) or [])
        lines.append("")
        lines.append("Vitality Metrics:")
        _append_metrics("vitality", signature.get("vitality", []) or [])
        lines.append("")
        lines.append("Life-Logistics Metrics:")
        _append_metrics("life_logistics", signature.get("lifeLogistics", []) or [])
        return lines

    def _render_pdf(self, lines: list[str]) -> bytes:
        page_width = 612
        page_height = 792
        margin = 50
        line_height = 14
        lines_per_page = max(1, (page_height - 2 * margin) // line_height)

        pages = [
            lines[i : i + lines_per_page]
            for i in range(0, len(lines), lines_per_page)
        ]

        def _escape_pdf_text(value: str) -> str:
            return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

        objects: list[str] = []
        pages_kids = []
        font_obj_num = 3

        for page_index, page_lines in enumerate(pages):
            page_obj_num = 4 + page_index * 2
            content_obj_num = page_obj_num + 1
            pages_kids.append(f"{page_obj_num} 0 R")

            text_lines = ["BT", "/F1 11 Tf"]
            y = page_height - margin
            for line in page_lines:
                escaped = _escape_pdf_text(str(line))
                text_lines.append(f"1 0 0 1 {margin} {y} Tm ({escaped}) Tj")
                y -= line_height
            text_lines.append("ET")
            content = "\n".join(text_lines)
            content_bytes = content.encode("latin-1")
            objects.append(
                "<< /Length {length} >>\nstream\n{content}\nendstream".format(
                    length=len(content_bytes),
                    content=content,
                )
            )

            page_obj = (
                "<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 {font} 0 R >> >> "
                "/MediaBox [0 0 {width} {height}] /Contents {content} 0 R >>"
            ).format(
                font=font_obj_num,
                width=page_width,
                height=page_height,
                content=content_obj_num,
            )
            objects.insert(-1, page_obj)

        pages_obj = "<< /Type /Pages /Kids [ {kids} ] /Count {count} >>".format(
            kids=" ".join(pages_kids),
            count=len(pages_kids),
        )
        catalog_obj = "<< /Type /Catalog /Pages 2 0 R >>"
        font_obj = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

        all_objects = [catalog_obj, pages_obj, font_obj] + objects

        pdf_parts: list[bytes] = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
        offsets = [0]
        current_length = len(pdf_parts[0])

        for idx, obj in enumerate(all_objects, start=1):
            obj_bytes = f"{idx} 0 obj\n{obj}\nendobj\n".encode("latin-1")
            offsets.append(current_length)
            pdf_parts.append(obj_bytes)
            current_length += len(obj_bytes)

        xref_offset = current_length
        xref_lines = ["xref", f"0 {len(all_objects) + 1}", "0000000000 65535 f "]
        for offset in offsets[1:]:
            xref_lines.append(f"{offset:010d} 00000 n ")
        xref = "\n".join(xref_lines).encode("latin-1")

        trailer = (
            "trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".format(
                size=len(all_objects) + 1,
                start=xref_offset,
            )
        ).encode("latin-1")

        pdf_parts.append(xref)
        pdf_parts.append(trailer)
        return b"".join(pdf_parts)

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
