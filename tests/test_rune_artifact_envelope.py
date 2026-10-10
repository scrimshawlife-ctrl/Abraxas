# tests/test_rune_artifact_envelope.py
from abx.execution_validation_types import wrap_in_rune_envelope


def test_wrap_in_rune_envelope():
    artifact = {"test": 1}
    e = wrap_in_rune_envelope(artifact, "RUNE.INGEST")
    assert e["rune_id"] == "RUNE.INGEST"
    assert e["payload"] == artifact
    assert e["schema"] == "rune_execution_artifact.v1"
    print("Envelope test passed")
