"""Trust Drift Graph Data: Time-series data for τₕ and IRI/MRI over time.

Format: JSON (time-series arrays for visualization)
Enables visualization of credibility erosion.
"""

from __future__ import annotations

import json
from typing import Dict, Any, List

from abraxas.core.provenance import Provenance


def generate_trust_drift_graph_json(
    time_series_data: List[Dict[str, Any]],
    provenance: Provenance,
) -> Dict[str, Any]:
    """
    Generate trust drift graph data in JSON format.

    Args:
        time_series_data: List of time-series points, each containing:
            - timestamp: ISO8601Z
            - tau_half_life: float
            - iri: float (optional)
            - mri: float (optional)
        provenance: Provenance record

    Returns:
        JSON-serializable dict with time-series arrays
    """
    timestamps = []
    tau_half_life_series = []
    iri_series = []
    mri_series = []

    for point in time_series_data:
        timestamps.append(point["timestamp"])
        tau_half_life_series.append(point.get("tau_half_life", None))
        iri_series.append(point.get("iri", None))
        mri_series.append(point.get("mri", None))

    return {
        "artifact_type": "trust_drift_graph_data",
        "data_points": len(time_series_data),
        "series": {
            "timestamps": timestamps,
            "tau_half_life": tau_half_life_series,
            "iri": iri_series,
            "mri": mri_series,
        },
        "provenance": provenance.__dict__,
    }


def write_trust_drift_graph_data(
    time_series_data: List[Dict[str, Any]],
    provenance: Provenance,
    output_path: str,
) -> None:
    """
    Write trust drift graph data to file (JSON only).

    Args:
        time_series_data: List of time-series points
        provenance: Provenance record
        output_path: Output file path
    """
    data = generate_trust_drift_graph_json(time_series_data, provenance)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
