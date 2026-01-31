from aal_core.beatoven.mappings import build_control_frame


def test_build_control_frame():
    terms = [
        {
            "term_id": "ghostmode",
            "drift_charge": 0.8,
            "directionality": "+",
            "half_life": 30,
            "domain_tags": ["culture"],
        }
    ]
    weather = {
        "volatility_index": 60,
        "compression_ratio": 2.0,
        "phase_bias": "attack",
        "noise_floor": 0.1,
    }
    context = {
        "kairos_window": "open",
        "ritual_density": 0.4,
        "symbolic_load": 0.7,
    }

    frame = build_control_frame(terms=terms, semiotic_weather=weather, oracle_context=context)

    assert frame.volatility == 0.6
    assert frame.velocity_scale == 0.5
    assert frame.tempo_shift_bpm == 2.0
    assert frame.symbolic_load_cc == 0.7
    assert frame.terms[0].modulation_depth == 0.8
