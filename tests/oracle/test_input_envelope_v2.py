from abraxas.oracle.runtime.input_normalizer import normalize_input_v2


def test_input_split_hashable_vs_display_only() -> None:
    raw = {
        "schema_id": "OracleSignalInputEnvelope.v2",
        "signal_sources": ["mda"],
        "payload": {"observations": []},
        "context": {},
        "metadata": {"run_id": "r1", "lane": "shadow", "tier": "advisory", "display_label": "x", "operator_note": "y"},
    }
    n = normalize_input_v2(raw)
    assert "display_label" in n["display_fields"]
    assert "operator_note" in n["display_fields"]
    assert "display_label" not in n["hashable_core"]["metadata"]
