from abx.bus.runtime import build_registry, process


def test_build_registry_is_sorted_and_stable():
    registry = build_registry()

    assert registry.list() == [
        "oracle",
        "rack",
        "semiotic",
        "slang_hist_seed_loader",
        "slang_seed_metrics_scorer",
        "weather",
    ]


def test_process_is_deterministic_for_same_payload():
    payload = {
        "intent": "chat",
        "user_text": "Hello Abraxas",
        "messages": [{"role": "user", "content": "Hello Abraxas"}],
    }

    frame_one = process(payload)
    frame_two = process(payload)

    assert frame_one == frame_two
    assert frame_one["meta"]["frame_id"].startswith("frame_")
    assert frame_one["output"]["status"] == "ok"
    assert "signal=" in frame_one["output"]["message"]


def test_process_respects_selected_modules_order_and_filtering():
    payload = {
        "intent": "chat",
        "user_text": "Signal check",
        "messages": [{"role": "user", "content": "Signal check"}],
        "selected_modules": ["semiotic", "unknown_module", "oracle"],
    }

    frame = process(payload)

    assert frame["meta"]["modules_executed"] == ["semiotic", "oracle"]
    assert set(frame["output"]["module_state"].keys()) == {"semiotic", "oracle"}
