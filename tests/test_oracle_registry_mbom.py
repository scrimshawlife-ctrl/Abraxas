from types import SimpleNamespace

from abraxas.oracle import registry


class _FakePipeline:
    def _forecast_phase(self, compression, run_id, git_sha):
        return SimpleNamespace(
            phase_transitions={"a": "NEXT"},
            resonance_score=0.5,
            resonating_domains=("d1",),
            weather_trajectory="steady",
            memetic_pressure=0.2,
            drift_velocity=0.1,
            provenance=SimpleNamespace(inputs_hash="h"),
        )


def test_run_overlay_emits_mbom_advisory(monkeypatch):
    monkeypatch.setattr(registry, "_get_pipeline", lambda: _FakePipeline())
    ctx = {
        "_compression": SimpleNamespace(
            lifecycle_states={"a": "SEED", "b": "STABLE"},
            domain_signals=("sig1",),
        ),
        "run_id": "r",
    }
    out = registry.run_overlay(ctx)
    assert out["status"] == "ok"
    assert out["mbom_v1"]["authority"] == "non-authoritative"
    assert ctx["_mbom_v1"]["lane"] == "support"
