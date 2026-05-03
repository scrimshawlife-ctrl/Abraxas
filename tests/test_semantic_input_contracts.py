import json
from pathlib import Path


from abraxas.semantic.contracts import attach_canonical_hash, canonical_hash


def test_contract_hashes_roundtrip():
    oracle = {"schema_version": "OracleInput.v1", "sources": [{"id": "s1"}], "signals": [{"lane": "SHADOW"}], "metadata": {"timestamp": "2026-05-03T00:00:00Z", "source_family": "local"}}
    oracle = attach_canonical_hash(oracle)
    assert oracle["canonical_hash"] == canonical_hash({k: v for k, v in oracle.items() if k != 'canonical_hash'})

    fo = {"schema_version": "ForecastOutcomeSet.v1", "forecasts": [{"id": "f1", "probability": 0.6, "label": "YES"}], "outcomes": [{"forecast_id": "f1", "resolved_value": 1}]}
    fo = attach_canonical_hash(fo)
    assert fo["canonical_hash"] == canonical_hash({k: v for k, v in fo.items() if k != 'canonical_hash'})

    canary = {"schema_version": "CanaryCandidateSet.v1", "candidates": [{"id": "c1", "target": "svc", "approval": "approved", "safety": "ok", "rollback_ready": True}]}
    canary = attach_canonical_hash(canary)
    assert canary["canonical_hash"] == canonical_hash({k: v for k, v in canary.items() if k != 'canonical_hash'})


def test_invalid_schema_rejected_paths():
    Path('out/oracle').mkdir(parents=True, exist_ok=True)
    Path('out/oracle/oracle_input.latest.json').write_text(json.dumps({"schema_version": "Bad.v1"}))
    Path('out/scoring').mkdir(parents=True, exist_ok=True)
    Path('out/scoring/forecast_outcome_set.latest.json').write_text(json.dumps({"schema_version": "Bad.v1"}))
    Path('out/canary').mkdir(parents=True, exist_ok=True)
    Path('out/canary/canary_candidate_set.latest.json').write_text(json.dumps({"schema_version": "Bad.v1"}))
