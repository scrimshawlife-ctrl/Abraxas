import json
from pathlib import Path

from abraxas.proof.proof_registry import build_registry, canonical_json


def _write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _seed(tmp_path: Path):
    repo = tmp_path / "out/proof/repo"
    runtime = tmp_path / "out/proofs/proof_artifact_001.latest.json"
    _write_json(repo / "repo_proof_manifest.latest.json", {"schema": "RepoProofManifest.v1"})
    _write_json(repo / "patch_coverage_map.latest.json", {"schema": "PatchCoverageMap.v1"})
    _write_json(repo / "repo_canon_alignment_report.latest.json", {"schema": "RepoCanonAlignmentReport.v1", "drift_class": "repo_ahead"})
    _write_json(repo / "repo_proof_receipt.latest.json", {"authority_boundary": "proof_only", "promotion_granted": False, "runtime_mutation": False})
    _write_json(runtime, {
        "lane": "SHADOW",
        "authority": {
            "production_activation": False,
            "canon_promotion": False,
            "baseline_mutation": False,
            "scheduler_mutation": False,
            "forecast_influence": False,
            "shadow_to_forecast_leakage": False,
            "runtime_mutation": False,
            "promotion_granted": False,
        },
        "validation": {"pointer_closure_status": "PASS"},
    })
    return repo, runtime


def test_deterministic_registry_build(tmp_path: Path):
    repo, runtime = _seed(tmp_path)
    r1 = build_registry(repo, runtime)
    r2 = build_registry(repo, runtime)
    assert canonical_json(r1) == canonical_json(r2)


def test_correct_ingestion_and_propagation(tmp_path: Path):
    repo, runtime = _seed(tmp_path)
    reg = build_registry(repo, runtime)
    assert reg["repo_proof"]["repo_canon_alignment_report"]["drift_class"] == "repo_ahead"
    assert reg["pointer_closure"] == "PASS"
    assert reg["combined_status"] == "LOCAL_CHAIN_PROVEN"


def test_authority_flags_false(tmp_path: Path):
    repo, runtime = _seed(tmp_path)
    reg = build_registry(repo, runtime)
    assert reg["authority_boundary"] == "proof_only"
    assert reg["promotion_granted"] is False
    assert reg["runtime_mutation"] is False
    assert reg["scheduler_write"] is False
    assert reg["forecast_influence"] is False
