from abraxas.registry.self_build_final_stack_runner import run_self_build_final_stack_runner

def test_final_stack_runner(): assert run_self_build_final_stack_runner()['schema_version']=='SelfBuildFinalStackResult.v1'
