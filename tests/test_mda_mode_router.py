from abraxas.mda.mode_router import render_mode


def test_mode_router_renders_all_modes():
    payload = {
        "envelope": {
            "env": "sandbox",
            "run_at": "2026-01-01T00:00:00Z",
            "seed": 1337,
            "input_hash": "x",
        },
        "domain_aggregates": {
            "tech_ai": {
                "status": "not_computable",
                "scores": {
                    "impact": 0.0,
                    "velocity": 0.0,
                    "uncertainty": 1.0,
                    "polarity": 0.0,
                },
            }
        },
        "dsp": [
            {
                "domain": "tech_ai",
                "subdomain": "foundation_models",
                "status": "not_computable",
                "scores": {
                    "impact": 0.0,
                    "velocity": 0.0,
                    "uncertainty": 1.0,
                    "polarity": 0.0,
                },
                "events": [],
                "evidence_refs": [],
            }
        ],
        "fusion_graph": {"nodes": {}, "edges": []},
    }

    for m in ("oracle", "ritual", "analyst"):
        r = render_mode(payload, mode=m)
        assert m in r.mode
        assert isinstance(r.markdown, str)
        assert len(r.markdown) > 10

