from abraxas.oracle.runtime.router import route_signal_item_v0


def test_router_stability() -> None:
    hot = route_signal_item_v0({"domain": "d", "subdomain": "s", "score": 0.9, "confidence": 0.9})
    watch = route_signal_item_v0({"domain": "d", "subdomain": "s", "score": 0.1, "confidence": 0.9})
    assert hot["tier"] == "hot"
    assert watch["tier"] == "watch"
