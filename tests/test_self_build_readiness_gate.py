from abraxas.registry.self_build_readiness_gate import run_self_build_readiness_gate

def test_readiness_gate(): assert run_self_build_readiness_gate()['schema_version']=='SelfBuildReadinessGate.v1'
