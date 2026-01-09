from abraxas.overlays.abx_gt_shadow import try_run_abx_gt_shadow


def test_abx_gt_shadow_hook_does_not_crash():
    out = try_run_abx_gt_shadow(
        seed=123,
        context={"oracle_date": "2026-01-09", "location": "Los Angeles, CA"},
    )
    assert "overlay" in out
    assert out["lane"] == "shadow"


def test_abx_gt_shadow_hook_determinism_when_installed():
    ctx = {"oracle_date": "2026-01-09", "location": "Los Angeles, CA"}
    a = try_run_abx_gt_shadow(seed=999, context=ctx)
    b = try_run_abx_gt_shadow(seed=999, context=ctx)
    assert a == b
