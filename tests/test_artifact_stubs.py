from pathlib import Path


def test_artifacts_exist() -> None:
    required = [
        "out/oracle/oracle_signal_packet.latest.json",
        "out/scoring/brier_scoring.latest.json",
        "out/canary/canary_activation_packet.latest.json",
    ]
    for path in required:
        assert Path(path).exists()
