from abraxas.viz.frontend_ci_proof_manifest import build_ci_proof_manifest


def test_ci_proof_manifest_determinism() -> None:
    a = build_ci_proof_manifest("failed_environment", "npm_registry_e403_access_restricted")
    b = build_ci_proof_manifest("failed_environment", "npm_registry_e403_access_restricted")
    assert a == b
    assert a["frontend_execution"] == "not_computable_environment"
    assert a["authority"]["interaction_runtime"] is False



def test_not_computable_environment_status_maps() -> None:
    m = build_ci_proof_manifest("not_computable_environment", "npm_registry_e403_access_restricted")
    assert m["frontend_execution"] == "not_computable_environment"
