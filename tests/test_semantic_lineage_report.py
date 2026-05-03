import json
from pathlib import Path
import subprocess

from abraxas.semantic.contracts import attach_canonical_hash


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def _seed_valid_chain(with_envelope: bool = True):
    oracle = {"schema_version": "OracleInput.v1", "sources": [{"id": "s1"}], "signals": [{"lane": "SHADOW"}], "metadata": {"timestamp": "2026-05-03T00:00:00Z", "source_family": "local"}}
    scoring = {"schema_version": "ForecastOutcomeSet.v1", "forecasts": [{"id": "f1", "probability": 0.5, "label": "YES"}], "outcomes": [{"forecast_id": "f1", "resolved_value": 1}]}
    canary = {"schema_version": "CanaryCandidateSet.v1", "candidates": [{"id": "c1", "target": "svc", "approval": "approved", "safety": "ok", "rollback_ready": True}]}
    if with_envelope:
        oracle["envelope"] = {"run_id": "RUN-A", "timestamp": "2026-05-03T00:00:00Z"}
        oracle_h = attach_canonical_hash(oracle)
        scoring["envelope"] = {"run_id": "RUN-B", "parent_run_id": "RUN-A", "timestamp": "2026-05-03T00:01:00Z", "source_hashes": [oracle_h["canonical_hash"]]}
        scoring_h = attach_canonical_hash(scoring)
        canary["envelope"] = {"run_id": "RUN-C", "parent_run_id": "RUN-B", "timestamp": "2026-05-03T00:02:00Z", "source_hashes": [scoring_h["canonical_hash"]]}
    _write("out/oracle/oracle_input.latest.json", attach_canonical_hash(oracle))
    _write("out/scoring/forecast_outcome_set.latest.json", attach_canonical_hash(scoring))
    _write("out/canary/canary_candidate_set.latest.json", attach_canonical_hash(canary))


def test_lineage_report_ready_with_links() -> None:
    _seed_valid_chain(with_envelope=True)
    subprocess.run(["python", "scripts/run_semantic_lineage_report.py"], check=True)
    out = json.loads(Path("out/semantic/semantic_lineage_report.latest.json").read_text())
    assert out["status"] == "LINEAGE_REPORT_READY"
    assert len(out["contracts"]) == 3
    assert any(link["valid"] for link in out["links"])


def test_lineage_report_not_computable_on_invalid_input() -> None:
    Path("out/oracle").mkdir(parents=True, exist_ok=True)
    Path("out/oracle/oracle_input.latest.json").write_text("{}", encoding="utf-8")
    _seed_valid_chain(with_envelope=False)
    Path("out/oracle/oracle_input.latest.json").write_text("{}", encoding="utf-8")
    subprocess.run(["python", "scripts/run_semantic_lineage_report.py"], check=True)
    out = json.loads(Path("out/semantic/semantic_lineage_report.latest.json").read_text())
    assert out["status"] == "NOT_COMPUTABLE"


def test_lineage_report_warns_missing_envelope() -> None:
    _seed_valid_chain(with_envelope=False)
    subprocess.run(["python", "scripts/run_semantic_lineage_report.py"], check=True)
    out = json.loads(Path("out/semantic/semantic_lineage_report.latest.json").read_text())
    assert out["status"] == "LINEAGE_REPORT_READY"
    assert any(w.startswith("missing_envelope:") for w in out["warnings"])
