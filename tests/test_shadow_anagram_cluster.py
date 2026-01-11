from abraxas.detectors.shadow.anagram import detect_shadow_anagrams
from abraxas.detectors.shadow.anagram_cluster import (
    init_cluster_state,
    update_anagram_clusters,
    emit_cluster_artifact,
    ClusterConfig,
    ClusterBudgets,
)


def test_cluster_update_is_deterministic_and_bounded():
    st = init_cluster_state()
    an = detect_shadow_anagrams(["Signal Layer", "Slang Drift"])
    cfg = ClusterConfig(budgets=ClusterBudgets(
        max_clusters=10,
        max_variants_per_cluster=5,
        max_src_tokens_per_cluster=5,
        max_domain_tags_per_cluster=5,
    ))

    st1 = update_anagram_clusters(
        st,
        anagram_artifact=an,
        context={"domain": "culture_memes", "subdomain": "slang_language_drift"},
        run_at_iso="2026-01-01T00:00:00Z",
        config=cfg,
    )
    st2 = update_anagram_clusters(
        st,
        anagram_artifact=an,
        context={"domain": "culture_memes", "subdomain": "slang_language_drift"},
        run_at_iso="2026-01-01T00:00:00Z",
        config=cfg,
    )

    art1 = emit_cluster_artifact(st1, config=cfg)
    art2 = emit_cluster_artifact(st2, config=cfg)
    assert art1["shadow_anagram_cluster_v1"]["artifact_hash"] == art2["shadow_anagram_cluster_v1"]["artifact_hash"]


def test_cluster_burst_flag():
    st = init_cluster_state()
    # fabricate many candidates under one source to trigger burst
    an = {
        "shadow_anagram_v1": {
            "candidates": [{"src": "Signal Layer", "dst": "Signal Layer"} for _ in range(6)],
            "not_computable": False,
        }
    }
    cfg = ClusterConfig(budgets=ClusterBudgets(max_clusters=10), burst_delta=5)
    st2 = update_anagram_clusters(
        st,
        anagram_artifact=an,
        context={"domain": "culture_memes", "subdomain": "slang_language_drift"},
        run_at_iso="2026-01-01T00:00:00Z",
        config=cfg,
    )
    art = emit_cluster_artifact(st2, config=cfg)
    clusters = art["shadow_anagram_cluster_v1"]["clusters"]
    assert len(clusters) >= 1
    assert clusters[0]["burst"] is True
