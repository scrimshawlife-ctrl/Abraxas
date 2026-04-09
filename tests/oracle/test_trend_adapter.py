from abraxas.oracle.advisory.trend_adapter import TrendAdapter


def test_trend_adapter_not_computable_visible() -> None:
    t = TrendAdapter()
    out = t.build(authority={}, normalized={"hashable_core": {"context": {}}})
    assert out["status"] == "NOT_COMPUTABLE"
    assert out["computable"] is False
