from __future__ import annotations

from abraxas_ase.anomaly import build_anomalies


def test_anomaly_determinism() -> None:
    metrics = {
        "pfdi_alerts": [
            ("2026-01-23", 1.0),
            ("2026-01-24", 4.0),
            ("2026-01-25", 2.0),
        ]
    }
    a1 = build_anomalies(metrics, window=2)
    a2 = build_anomalies(metrics, window=2)
    assert a1 == a2
