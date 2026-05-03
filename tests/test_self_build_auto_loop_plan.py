from abraxas.registry.self_build_auto_loop_plan import run_self_build_auto_loop_plan

def test_auto_loop_plan(): assert run_self_build_auto_loop_plan()['schema_version']=='SelfBuildAutoLoopPlan.v1'
