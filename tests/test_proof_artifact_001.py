import json
from pathlib import Path

from scripts.build_runtime_chain_proof_artifact import build_proof_artifact, canonical_json


def test_pointer_closure_requirements_and_attested_status():
    art = build_proof_artifact("2026-05-01T00:00:00Z", "s", "o", "x")
    c = art["correlation"]
    assert c["packetIds"]
    assert c["ledgerRecordIds"]
    assert c["validatorArtifactId"]
    assert len(c["input_hash"]) == 64
    assert art["execution_status"] == "ATTESTED"
    assert art["validation"]["pointer_closure_status"] == "PASS"


def test_failure_status_when_pointers_missing():
    art = build_proof_artifact("2026-05-01T00:00:00Z", "s", "o", "x", force_pointer_failure=True)
    assert art["correlation"]["packetIds"] == []
    assert art["execution_status"] == "NOT_COMPUTABLE_POINTER_CLOSURE"
    assert art["validation"]["pointer_closure_status"] == "FAIL"


def test_authority_flags_false_and_shadow_lane():
    art = build_proof_artifact("2026-05-01T00:00:00Z", "s", "o", "x")
    assert art["lane"] == "SHADOW"
    assert all(v is False for v in art["authority"].values())


def test_byte_identical_rerun_and_proof_hash_reproducible():
    a1 = build_proof_artifact("2026-05-01T00:00:00Z", "s", "o", "x")
    a2 = build_proof_artifact("2026-05-01T00:00:00Z", "s", "o", "x")
    assert canonical_json(a1) == canonical_json(a2)
    assert a1["proof_hash"] == a2["proof_hash"]


def test_canonical_json_final_newline(tmp_path: Path):
    art = build_proof_artifact("2026-05-01T00:00:00Z", "s", "o", "x")
    out = tmp_path / "a.json"
    out.write_text(canonical_json(art), encoding="utf-8")
    raw = out.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    loaded = json.loads(raw)
    assert loaded["schema_version"] == "ProofArtifact.v1"
