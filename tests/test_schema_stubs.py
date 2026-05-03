from pathlib import Path


def test_schema_stubs_exist() -> None:
    required = [
        "schemas/OracleSignalPacket.v1.schema.json",
        "schemas/BrierScoringRun.v1.schema.json",
        "schemas/CanaryActivationPacket.v1.schema.json",
        "schemas/AALVizProofState.v1.schema.json",
        "schemas/ProofStatusCard.v1.schema.json",
    ]
    for path in required:
        assert Path(path).exists()
