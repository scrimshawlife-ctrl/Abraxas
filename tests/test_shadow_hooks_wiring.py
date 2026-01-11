import json
import os

from abraxas.mda.shadow_hooks import apply_shadow_anagram_detectors


def test_shadow_hooks_attach_anagram_blocks_and_persist_state(tmp_path):
    out_dir = str(tmp_path / "out")
    payload = {
        "vectors": {
            "culture_memes": {
                "slang_language_drift": {
                    "scores": {"impact": 0.2, "velocity": 0.8, "uncertainty": 0.5, "polarity": 0.1},
                    "events": [{"title": "Signal Layer", "tags": ["meme:signal_layer"], "evidence_refs": ["ref:1"]}],
                    "evidence_refs": ["ref:root"],
                }
            }
        }
    }
    mda_out = {"envelope": {"env": "sandbox"}, "domain_aggregates": {}, "dsp": [], "fusion_graph": {}}
    out2 = apply_shadow_anagram_detectors(
        mda_out=mda_out,
        payload=payload,
        context={"domain": "culture_memes", "subdomain": "slang_language_drift"},
        run_at_iso="2026-01-01T00:00:00Z",
        out_dir=out_dir,
        watchlist_tokens=("Signal Layer",),
    )
    assert "shadow" in out2
    sh = out2["shadow"]
    assert "anagram_v1" in sh
    assert "anagram_cluster_v1" in sh

    state_path = os.path.join(out_dir, "shadow_state", "anagram_cluster_state.json")
    assert os.path.exists(state_path)
    with open(state_path, "r", encoding="utf-8") as f:
        st = json.load(f)
    assert "clusters" in st
    assert "watch" in st
