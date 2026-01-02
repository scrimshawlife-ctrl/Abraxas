from abraxas.mda.signal_layer_v2 import mda_to_oracle_signal_v2, shallow_schema_check


def test_signal_v2_emission_is_stable_and_has_hash():
    mda_out = {
        "envelope": {"env": "sandbox", "run_at": "2026-01-01T00:00:00Z", "seed": 1337, "input_hash": "abc"},
        "domain_aggregates": {
            "tech_ai": {
                "status": "ok",
                "scores": {"impact": 0.2, "velocity": 0.2, "uncertainty": 0.8, "polarity": 0.0},
                "subdomains": ["foundation_models"],
                "evidence_refs": [],
            }
        },
        "dsp": [
            {
                "domain": "tech_ai",
                "subdomain": "foundation_models",
                "status": "ok",
                "scores": {"impact": 0.2, "velocity": 0.2, "uncertainty": 0.8, "polarity": 0.0},
                "events": [
                    {
                        "event_id": "evt_123456",
                        "title": "X",
                        "time": "2026-01-01T00:00:00Z",
                        "claims": [{"claim": "C", "confidence": 0.5, "evidence_refs": ["ref:1"]}],
                        "tags": ["meme:test"],
                        "metrics": {},
                    }
                ],
                "evidence_refs": [],
                "provenance": {"module": "x", "version": "y", "input_hash": "abc", "run_seed": 1337},
            }
        ],
        "fusion_graph": {"nodes": {"evt_123456": {}}, "edges": []},
    }
    sig = mda_to_oracle_signal_v2(mda_out)
    shallow_schema_check(sig)

    osv2 = sig["oracle_signal_v2"]
    assert osv2["meta"]["slice_hash"]
    # evidence gating: since dsp evidence_refs is empty, claim evidence_refs should be omitted
    claims = osv2["mda_v1_1"]["dsp"][0]["events"][0]["claims"][0]
    assert "evidence_refs" not in claims


def test_signal_v2_includes_evidence_refs_when_present():
    mda_out = {
        "envelope": {"env": "sandbox", "run_at": "2026-01-01T00:00:00Z", "seed": 1337, "input_hash": "abc"},
        "domain_aggregates": {},
        "dsp": [
            {
                "domain": "tech_ai",
                "subdomain": "foundation_models",
                "status": "ok",
                "scores": {"impact": 0.2, "velocity": 0.2, "uncertainty": 0.8, "polarity": 0.0},
                "events": [
                    {
                        "event_id": "evt_123456",
                        "title": "X",
                        "time": "2026-01-01T00:00:00Z",
                        "claims": [{"claim": "C", "confidence": 0.5, "evidence_refs": ["ref:1"]}],
                        "tags": ["meme:test"],
                        "metrics": {},
                    }
                ],
                "evidence_refs": ["ref:root"],
                "provenance": {"module": "x", "version": "y", "input_hash": "abc", "run_seed": 1337},
            }
        ],
        "fusion_graph": {"nodes": {"evt_123456": {}}, "edges": []},
    }
    sig = mda_to_oracle_signal_v2(mda_out)
    claims = sig["oracle_signal_v2"]["mda_v1_1"]["dsp"][0]["events"][0]["claims"][0]
    assert "evidence_refs" in claims

