from __future__ import annotations

import json
from pathlib import Path

from abraxas.artifacts.integrity_brief import generate_integrity_brief


def _sample_inputs():
    ledger_health = {"total_ledgers": 5, "healthy_ledgers": 5, "hash_chain_valid": True}
    delta_counts = {"new_terms": 3, "mw_shifts": 2, "tau_updates": 5}
    anomaly_flags: list[str] = []
    timestamp = "2025-12-26T00:00:00.000000Z"
    return ledger_health, delta_counts, anomaly_flags, timestamp


def test_brief_generation():
    ledger_health, delta_counts, anomaly_flags, timestamp = _sample_inputs()
    brief_json, brief_md = generate_integrity_brief(
        ledger_health_metrics=ledger_health,
        delta_counts=delta_counts,
        anomaly_flags=anomaly_flags,
        timestamp=timestamp,
    )

    json_path = Path("tests/golden/artifacts/integrity_brief_sample.json")
    md_path = Path("tests/golden/artifacts/integrity_brief_sample.md")

    expected_json = json.loads(json_path.read_text(encoding="utf-8"))
    expected_md = md_path.read_text(encoding="utf-8").strip()

    assert brief_json == expected_json
    assert brief_md.strip() == expected_md


def test_brief_completeness():
    ledger_health, delta_counts, anomaly_flags, timestamp = _sample_inputs()
    brief_json, brief_md = generate_integrity_brief(
        ledger_health_metrics=ledger_health,
        delta_counts=delta_counts,
        anomaly_flags=anomaly_flags,
        timestamp=timestamp,
    )

    assert brief_json["sections"] == [
        "summary",
        "ledger_health",
        "delta_analysis",
        "anomaly_detection",
        "recommendations",
    ]
    assert brief_json["delta_counts"]["total_deltas"] == 10
    assert "Integrity Brief" in brief_md
