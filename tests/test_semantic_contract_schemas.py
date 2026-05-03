import json
from pathlib import Path

import pytest

from abraxas.semantic.contracts import ContractLoadError, attach_canonical_hash, load_contract


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def test_valid_contract_passes() -> None:
    payload = attach_canonical_hash({"schema_version": "ForecastOutcomeSet.v1", "forecasts": [{"id": "f1", "probability": 0.7, "label": "YES"}], "outcomes": [{"forecast_id": "f1", "resolved_value": 1}]})
    _write("out/scoring/forecast_outcome_set.latest.json", payload)
    loaded = load_contract("out/scoring/forecast_outcome_set.latest.json", "ForecastOutcomeSet.v1")
    assert loaded["schema_version"] == "ForecastOutcomeSet.v1"


def test_missing_required_field_fails() -> None:
    payload = attach_canonical_hash({"schema_version": "ForecastOutcomeSet.v1", "forecasts": [{"id": "f1", "probability": 0.7, "label": "YES"}]})
    _write("out/scoring/forecast_outcome_set.latest.json", payload)
    with pytest.raises(ContractLoadError) as exc:
        load_contract("out/scoring/forecast_outcome_set.latest.json", "ForecastOutcomeSet.v1")
    assert exc.value.reason == "INVALID_SCHEMA"


def test_wrong_type_fails() -> None:
    payload = attach_canonical_hash({"schema_version": "CanaryCandidateSet.v1", "candidates": [{"id": "c1", "target": "svc", "approval": "approved", "safety": "ok", "rollback_ready": "yes"}]})
    _write("out/canary/canary_candidate_set.latest.json", payload)
    with pytest.raises(ContractLoadError) as exc:
        load_contract("out/canary/canary_candidate_set.latest.json", "CanaryCandidateSet.v1")
    assert exc.value.reason == "INVALID_SCHEMA"


def test_invalid_enum_fails() -> None:
    payload = attach_canonical_hash({"schema_version": "OracleInput.v1", "sources": [{"id": "s1"}], "signals": [{"lane": "BAD"}], "metadata": {"timestamp": "2026-05-03T00:00:00Z", "source_family": "local"}})
    _write("out/oracle/oracle_input.latest.json", payload)
    with pytest.raises(ContractLoadError) as exc:
        load_contract("out/oracle/oracle_input.latest.json", "OracleInput.v1")
    assert exc.value.reason == "INVALID_SCHEMA"


def test_envelope_validation_pass_fail_and_hash_stability() -> None:
    base = {"schema_version": "OracleInput.v1", "sources": [{"id": "s1"}], "signals": [{"lane": "SHADOW"}], "metadata": {"timestamp": "2026-05-03T00:00:00Z", "source_family": "local"}, "envelope": {"run_id": "RUN-1", "timestamp": "2026-05-03T00:00:00Z", "source_hashes": ["h1"]}}
    good = attach_canonical_hash(base)
    _write("out/oracle/oracle_input.latest.json", good)
    loaded = load_contract("out/oracle/oracle_input.latest.json", "OracleInput.v1")
    assert loaded["envelope"]["run_id"] == "RUN-1"

    bad = attach_canonical_hash({**base, "envelope": {"timestamp": "2026-05-03T00:00:00Z"}})
    _write("out/oracle/oracle_input.latest.json", bad)
    with pytest.raises(ContractLoadError) as exc:
        load_contract("out/oracle/oracle_input.latest.json", "OracleInput.v1")
    assert exc.value.reason == "INVALID_SCHEMA"


def test_cross_contract_linkage_simulation() -> None:
    oracle = attach_canonical_hash({"schema_version": "OracleInput.v1", "sources": [{"id": "s1"}], "signals": [{"lane": "SHADOW"}], "metadata": {"timestamp": "2026-05-03T00:00:00Z", "source_family": "local"}, "envelope": {"run_id": "RUN-A", "timestamp": "2026-05-03T00:00:00Z"}})
    scoring = attach_canonical_hash({"schema_version": "ForecastOutcomeSet.v1", "forecasts": [{"id": "f1", "probability": 0.5, "label": "YES"}], "outcomes": [{"forecast_id": "f1", "resolved_value": 1}], "envelope": {"run_id": "RUN-B", "parent_run_id": "RUN-A", "timestamp": "2026-05-03T00:01:00Z", "source_hashes": [oracle["canonical_hash"]]}})
    canary = attach_canonical_hash({"schema_version": "CanaryCandidateSet.v1", "candidates": [{"id": "c1", "target": "svc", "approval": "approved", "safety": "ok", "rollback_ready": True}], "envelope": {"run_id": "RUN-C", "parent_run_id": "RUN-B", "timestamp": "2026-05-03T00:02:00Z", "source_hashes": [scoring["canonical_hash"]]}})
    assert scoring["envelope"]["source_hashes"][0] == oracle["canonical_hash"]
    assert canary["envelope"]["source_hashes"][0] == scoring["canonical_hash"]
