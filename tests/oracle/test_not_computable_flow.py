from __future__ import annotations

from abraxas.oracle.proof.validator_summary import build_validator_summary_v2
from abraxas.oracle.runtime.service import run_oracle_signal_layer_v2_service
from abraxas.oracle.stability.digests import compute_digest_triplet
from abraxas.oracle.runtime.input_normalizer import normalize_input_v2


def test_missing_observations_marks_output_not_computable() -> None:
    raw = {
        "schema_id": "OracleSignalInputEnvelope.v2",
        "signal_sources": ["mda"],
        "payload": {"observations": []},
        "context": {},
        "metadata": {"run_id": "r_nc", "lane": "shadow", "tier": "advisory"},
    }
    out = run_oracle_signal_layer_v2_service(raw)
    assert out["provenance"]["computable"] is False
    assert out["provenance"]["status"] == "NOT_COMPUTABLE"
    assert "missing_observations" in out["provenance"]["not_computable_reasons"]


def test_validator_summary_blocks_when_output_not_computable() -> None:
    raw = {
        "schema_id": "OracleSignalInputEnvelope.v2",
        "signal_sources": ["mda"],
        "payload": {"observations": []},
        "context": {},
        "metadata": {"run_id": "r_nc2", "lane": "shadow", "tier": "advisory"},
    }
    out = run_oracle_signal_layer_v2_service(raw)
    hashes = compute_digest_triplet(normalized=normalize_input_v2(raw), output=out)
    summary = build_validator_summary_v2(output=out, hashes=hashes, artifact_refs=[])
    assert summary["status"] == "BLOCKED"
