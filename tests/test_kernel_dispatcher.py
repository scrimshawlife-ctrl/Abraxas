from types import SimpleNamespace

from abraxas.kernel import dispatcher


def test_get_kernel_runner_returns_registered_runner(monkeypatch):
    def fake_runner(_inputs):
        return {"ok": True}

    monkeypatch.setattr(dispatcher, "_load_runner", lambda _path: (fake_runner, None))

    runner = dispatcher.get_kernel_runner("v2")
    result = runner(SimpleNamespace())
    assert result == {"ok": True}


def test_get_kernel_runner_unknown_version_falls_back_to_default(monkeypatch):
    calls = {}

    def fake_load(path):
        calls["path"] = path
        return (lambda _inputs: {"path": path}, None)

    monkeypatch.setattr(dispatcher, "_load_runner", fake_load)

    runner = dispatcher.get_kernel_runner("nonexistent")
    result = runner(SimpleNamespace())

    assert calls["path"] == dispatcher.KERNEL_REGISTRY["v2"]
    assert result["path"] == dispatcher.KERNEL_REGISTRY["v2"]


def test_get_kernel_runner_returns_deterministic_error_envelope_when_unloadable(monkeypatch):
    monkeypatch.setattr(dispatcher, "_load_runner", lambda _path: (None, "boom"))

    runner = dispatcher.get_kernel_runner("v2")
    inputs = SimpleNamespace(
        day="2026-03-27",
        user={"location_label": "Austin"},
        overlays_enabled={"neon_genie": False},
        tier_ctx={"tier": "SOLO"},
    )
    result = runner(inputs)

    assert result["header"]["headline"] == "Kernel entrypoint unavailable."
    assert result["not_computable"]["reason"] == "kernel_runner_unavailable"
    assert result["not_computable"]["details"] == "boom"
    assert "stub" not in result["vector_mix"]["notes"].lower()
