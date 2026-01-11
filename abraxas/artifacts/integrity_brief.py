"""Integrity Brief Generator.

Summarizes ledger health, delta activity, and anomaly flags in JSON/Markdown.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


SECTIONS = [
    "summary",
    "ledger_health",
    "delta_analysis",
    "anomaly_detection",
    "recommendations",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass(frozen=True)
class LedgerHealth:
    total_ledgers: int
    healthy_ledgers: int
    hash_chain_valid: bool

    @classmethod
    def from_metrics(cls, metrics: Dict[str, Any], hash_chain_status: Optional[bool]) -> "LedgerHealth":
        total = int(metrics.get("total_ledgers", 0))
        healthy = int(metrics.get("healthy_ledgers", total))
        hash_chain_valid = bool(
            metrics.get("hash_chain_valid", hash_chain_status if hash_chain_status is not None else True)
        )
        return cls(total_ledgers=total, healthy_ledgers=healthy, hash_chain_valid=hash_chain_valid)


def _normalize_delta_counts(delta_counts: Dict[str, Any]) -> Dict[str, int]:
    new_terms = int(delta_counts.get("new_terms", 0))
    mw_shifts = int(delta_counts.get("mw_shifts", 0))
    tau_updates = int(delta_counts.get("tau_updates", 0))
    total_deltas = int(delta_counts.get("total_deltas", new_terms + mw_shifts + tau_updates))
    return {
        "new_terms": new_terms,
        "mw_shifts": mw_shifts,
        "tau_updates": tau_updates,
        "total_deltas": total_deltas,
    }


def build_integrity_brief(
    *,
    ledger_health_metrics: Dict[str, Any],
    delta_counts: Dict[str, Any],
    anomaly_flags: List[str],
    hash_chain_status: Optional[bool] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    ledger_health = LedgerHealth.from_metrics(ledger_health_metrics, hash_chain_status)
    deltas = _normalize_delta_counts(delta_counts)
    brief_ts = timestamp or _utc_now_iso()

    return {
        "timestamp": brief_ts,
        "ledger_health": {
            "total_ledgers": ledger_health.total_ledgers,
            "healthy_ledgers": ledger_health.healthy_ledgers,
            "hash_chain_valid": ledger_health.hash_chain_valid,
        },
        "delta_counts": deltas,
        "anomaly_flags": list(anomaly_flags),
        "sections": list(SECTIONS),
    }


def _status_line(brief: Dict[str, Any]) -> Tuple[str, str]:
    ledger = brief.get("ledger_health", {})
    anomalies = brief.get("anomaly_flags", [])
    healthy = (
        int(ledger.get("total_ledgers", 0)) == int(ledger.get("healthy_ledgers", 0))
        and bool(ledger.get("hash_chain_valid", False))
        and not anomalies
    )
    status = "HEALTHY" if healthy else "ATTENTION"
    marker = "✓" if healthy else "!"
    return status, marker


def render_integrity_brief_markdown(brief: Dict[str, Any]) -> str:
    status, marker = _status_line(brief)
    ledger = brief.get("ledger_health", {})
    deltas = brief.get("delta_counts", {})
    anomalies = brief.get("anomaly_flags", [])
    ts = brief.get("timestamp", "")
    date_str = ts.split("T", 1)[0] if ts else ""

    summary_line = (
        f"All ledgers healthy. Hash chain validation passed. {deltas.get('total_deltas', 0)} deltas "
        "observed in this period."
        if status == "HEALTHY"
        else "Ledger health requires attention. Review anomaly flags and hash chain status."
    )

    anomaly_section = (
        "\n".join(f"- {flag}" for flag in anomalies) if anomalies else "No anomalies detected."
    )

    recommendations = (
        "Continue normal operations. No action required."
        if status == "HEALTHY"
        else "Investigate anomalies and validate ledger integrity before release."
    )

    return "\n".join(
        [
            "# Integrity Brief",
            "",
            f"**Date**: {date_str}",
            f"**Status**: {status} {marker}",
            "",
            "---",
            "",
            "## Summary",
            "",
            summary_line,
            "",
            "---",
            "",
            "## Ledger Health",
            "",
            f"- **Total Ledgers**: {ledger.get('total_ledgers', 0)}",
            f"- **Healthy Ledgers**: {ledger.get('healthy_ledgers', 0)}",
            f"- **Hash Chain Valid**: {'✓ Yes' if ledger.get('hash_chain_valid') else '✗ No'}",
            "",
            "---",
            "",
            "## Delta Analysis",
            "",
            f"- **New Terms**: {deltas.get('new_terms', 0)}",
            f"- **MW Shifts**: {deltas.get('mw_shifts', 0)}",
            f"- **TAU Updates**: {deltas.get('tau_updates', 0)}",
            f"- **Total Deltas**: {deltas.get('total_deltas', 0)}",
            "",
            "---",
            "",
            "## Anomaly Detection",
            "",
            anomaly_section,
            "",
            "---",
            "",
            "## Recommendations",
            "",
            recommendations,
            "",
        ]
    )


def generate_integrity_brief(
    *,
    ledger_health_metrics: Dict[str, Any],
    delta_counts: Dict[str, Any],
    anomaly_flags: List[str],
    hash_chain_status: Optional[bool] = None,
    timestamp: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    brief = build_integrity_brief(
        ledger_health_metrics=ledger_health_metrics,
        delta_counts=delta_counts,
        anomaly_flags=anomaly_flags,
        hash_chain_status=hash_chain_status,
        timestamp=timestamp,
    )
    markdown = render_integrity_brief_markdown(brief)
    return brief, markdown


__all__ = ["build_integrity_brief", "generate_integrity_brief", "render_integrity_brief_markdown"]
