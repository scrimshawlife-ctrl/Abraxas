from __future__ import annotations
from abraxas.core.kernel import AbraxasKernel
from abraxas.core.context import UserContext
from abraxas.kite.shadow_replay import shadow_replay


def test_kite_shadow_replay_runs():
    k = AbraxasKernel()
    admin = frozenset({"admin"})
    u = UserContext(user_id="x", tier="academic")

    base = {"pressure": 3, "motifs": ["audio"]}
    injected = {"pressure": 6, "motifs": ["audio", "midi"]}

    out = shadow_replay(
        kernel=k,
        admin_perms=admin,
        user=u,
        base_signals=base,
        injected_signals=injected,
        overlays=["aalmanac", "beatoven"],
    )
    assert "base_run" in out and "injected_run" in out
