from __future__ import annotations

from abraxas.oracle.runtime.input_normalizer import normalize_input_v2
from abraxas.oracle.runtime.service import run_oracle_signal_layer_v2_service
from abraxas.oracle.stability.digests import compute_digest_triplet


def _base(label: str) -> dict:
    return {
        "schema_id": "OracleSignalInputEnvelope.v2",
        "signal_sources": ["mda"],
        "payload": {"observations": [{"domain": "d", "subdomain": "s", "score": 0.5, "confidence": 0.7, "age_hours": 1}]},
        "context": {},
        "metadata": {"run_id": "r1", "lane": "shadow", "tier": "advisory", "display_label": label, "operator_note": label},
    }


def test_display_only_metadata_does_not_change_authority_digest() -> None:
    a = _base("alpha")
    b = _base("beta")
    out_a = run_oracle_signal_layer_v2_service(a)
    out_b = run_oracle_signal_layer_v2_service(b)
    dig_a = compute_digest_triplet(normalized=normalize_input_v2(a), output=out_a)
    dig_b = compute_digest_triplet(normalized=normalize_input_v2(b), output=out_b)
    assert dig_a["authority_hash"] == dig_b["authority_hash"]
