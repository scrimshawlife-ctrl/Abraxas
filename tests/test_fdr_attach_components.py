"""
Tests for attaching FDR components during ensemble updates.
"""

from datetime import datetime, timezone

from abraxas.forecast.init import init_ensemble_state
from abraxas.forecast.types import Horizon
from abraxas.forecast.update import InfluenceEvent, apply_influence_to_ensemble


def test_fdr_attach_components():
    ensemble = init_ensemble_state(
        topic_key="term_cluster:alpha",
        horizon=Horizon.H30D,
        segment="core",
        narrative="N1_primary",
    )

    influence = InfluenceEvent(
        influence_id="inf_term_velocity",
        target="MRI_push",
        strength=0.5,
        provenance={"term_velocity": 0.9},
    )

    updated = apply_influence_to_ensemble(
        ensemble=ensemble,
        influence_events=[influence],
        integrity_snapshot={"SSI": 0.2},
        now_ts=datetime(2025, 12, 26, tzinfo=timezone.utc),
    )

    delta_summary = updated.provenance["last_update"]["delta_summary"]
    components = delta_summary["components"]

    assert components == [
        {"component_id": "FDR_SLANG_HANDLE_EMERGENCE", "weight": 0.5}
    ]
