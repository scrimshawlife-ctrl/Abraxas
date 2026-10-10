# tests/test_snapshot_exact_match.py
from abraxas.engines.execution_harness import get_synthesis_label


def test_exact_match_maps_to_non_degraded():
    # simulate bound exact
    label = get_synthesis_label("EXACT_MATCH", blocker=None)
    assert label != "DEGRADED"
    print("Snapshot exact match test passed")
