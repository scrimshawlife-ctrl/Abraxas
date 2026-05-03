from abraxas.operator.self_build_operator_packet import run_self_build_operator_packet

def test_operator_packet(): assert run_self_build_operator_packet()['schema_version']=='SelfBuildOperatorPacket.v1'
