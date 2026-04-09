from abraxas.oracle.stability.invariance import run_invariance_v2


BASE = {
    "schema_id": "OracleSignalInputEnvelope.v2",
    "signal_sources": ["mda"],
    "payload": {"observations": [{"domain": "d", "subdomain": "s", "score": 0.5, "confidence": 0.7, "age_hours": 1}]},
    "context": {},
    "metadata": {"run_id": "r1", "lane": "shadow", "tier": "advisory", "display_label": "a"},
}


def test_invariance_passes_on_identical_input() -> None:
    rep = run_invariance_v2(BASE, repeats=4)
    assert rep["status"] == "PASS"
