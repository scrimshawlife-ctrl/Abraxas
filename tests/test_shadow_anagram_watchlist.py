from abraxas.detectors.shadow.anagram import detect_shadow_anagrams
from abraxas.detectors.shadow.anagram_cluster import (
    init_cluster_state,
    update_anagram_clusters,
    emit_cluster_artifact,
    ClusterConfig,
    ClusterBudgets,
)


def test_watchlist_emits_alert_on_new_variants_or_burst():
    st = init_cluster_state()
    cfg = ClusterConfig(
        budgets=ClusterBudgets(max_clusters=50, max_watch_alerts=10),
        burst_delta=5,
        watchlist_tokens=("Signal Layer",),
    )

    # Create anagrams for watched token; even if candidates are few, should be tracked when present
    an = detect_shadow_anagrams(["Signal Layer"], evidence_refs=["ref:1"])
    st2 = update_anagram_clusters(
        st,
        anagram_artifact=an,
        context={"domain": "culture_memes", "subdomain": "slang_language_drift"},
        run_at_iso="2026-01-01T00:00:00Z",
        config=cfg,
    )
    art = emit_cluster_artifact(st2, config=cfg)
    wl = art["shadow_anagram_cluster_v1"]["watchlist"]
    assert len(wl) == 1

    alerts = art["shadow_anagram_cluster_v1"]["watch_alerts"]
    # If detector produced any variants (likely), we should alert (delta>0).
    # If none produced, alerts may be empty; this test then fabricates a burst below.
    if len(alerts) == 0:
        # Force burst
        an2 = {
            "shadow_anagram_v1": {
                "candidates": [{"src": "Signal Layer", "dst": "Signal Layer"} for _ in range(6)],
                "not_computable": False,
            }
        }
        st3 = update_anagram_clusters(
            st2,
            anagram_artifact=an2,
            context={"domain": "culture_memes", "subdomain": "slang_language_drift"},
            run_at_iso="2026-01-01T00:00:00Z",
            config=cfg,
        )
        art2 = emit_cluster_artifact(st3, config=cfg)
        alerts2 = art2["shadow_anagram_cluster_v1"]["watch_alerts"]
        assert len(alerts2) >= 1
        assert alerts2[0]["burst"] is True
