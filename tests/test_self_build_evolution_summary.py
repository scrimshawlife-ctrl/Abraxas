from abraxas.registry.self_build_evolution_summary import run_self_build_evolution_summary

def test_evolution_summary(): assert run_self_build_evolution_summary()['schema_version']=='SelfBuildEvolutionSummary.v1'
