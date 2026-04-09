from copy import deepcopy

from abraxas.oracle.runtime.service import run_oracle_signal_layer_v2_service


BASE = {
    "schema_id": "OracleSignalInputEnvelope.v2",
    "signal_sources": ["mda"],
    "payload": {"observations": [{"domain": "d", "subdomain": "s", "score": 0.5, "confidence": 0.7, "age_hours": 1}]},
    "context": {},
    "metadata": {"run_id": "r1", "lane": "shadow", "tier": "advisory"},
}


def test_advisory_cannot_mutate_authority() -> None:
    out = run_oracle_signal_layer_v2_service(BASE)
    authority_before = deepcopy(out["authority"])
    out["advisory_attachments"][0]["payload"]["meaning_pressure"] = 999  # mutate advisory only
    assert out["authority"] == authority_before
