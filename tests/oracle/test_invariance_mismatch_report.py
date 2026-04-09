from abraxas.oracle.stability.mismatch_report import build_mismatch_report


def test_mismatch_report_shape() -> None:
    rep = build_mismatch_report(input_hashes=["a", "b"], authority_hashes=["c", "d"], full_hashes=["e", "f"])
    assert rep["status"] == "MISMATCH"
    assert rep["input_hashes"] == ["a", "b"]
