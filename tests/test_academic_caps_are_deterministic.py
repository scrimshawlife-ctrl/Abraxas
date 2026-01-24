from __future__ import annotations

from abraxas_ase.tiering import apply_tier


def test_academic_caps_are_deterministic() -> None:
    hits = []
    clusters = {}
    for i in range(12):
        item_id = f"item-{i}"
        clusters[item_id] = f"cluster-{i % 2}"
        hits.append(
            {
                "token": "alpha",
                "sub": "omega",
                "lane": "core",
                "item_id": item_id,
                "source": "ap",
                "tier": 2,
                "verified": True,
            }
        )
    report = {
        "date": "2026-01-24",
        "version": "0.1.0",
        "schema_versions": {"ase_output": "v0.1"},
        "stats": {"tier2_hits": len(hits)},
        "run_id": "run",
        "verified_sub_anagrams": hits,
        "clusters": {"by_item_id": clusters, "cluster_key_version": 1},
        "sas": {"params": {}, "rows": []},
        "pfdi_alerts": [],
        "runtime_lexicon": {},
    }
    filtered = apply_tier(report, tier="academic", safe_export=True, include_urls=False)
    filtered_hits = filtered["verified_sub_anagrams"]
    assert len(filtered_hits) <= 5
    assert filtered_hits == sorted(filtered_hits, key=lambda h: (h["sub"], h["token"], h["source"], h["item_id"]))
