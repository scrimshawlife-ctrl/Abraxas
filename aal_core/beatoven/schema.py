AALMANAC_INPUT_SCHEMA = {
    "schema_version": "aal.beatoven.aalmanac_input.v1",
    "type": "object",
    "required": ["terms"],
    "properties": {
        "terms": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "term_id",
                    "drift_charge",
                    "directionality",
                    "half_life",
                    "domain_tags",
                ],
                "properties": {
                    "term_id": {"type": "string"},
                    "drift_charge": {"type": "number", "minimum": 0, "maximum": 1},
                    "directionality": {"type": "string", "enum": ["+", "-", "oscillatory"]},
                    "half_life": {"type": "number", "minimum": 0.1, "maximum": 365},
                    "domain_tags": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    },
}

SEMIOTIC_WEATHER_SCHEMA = {
    "schema_version": "aal.beatoven.semiotic_weather.v1",
    "type": "object",
    "required": ["volatility_index", "compression_ratio", "phase_bias", "noise_floor"],
    "properties": {
        "volatility_index": {"type": "number", "minimum": 0, "maximum": 100},
        "compression_ratio": {"type": "number", "minimum": 0, "maximum": 10},
        "phase_bias": {"type": "string", "enum": ["attack", "sustain", "decay"]},
        "noise_floor": {"type": "number", "minimum": 0, "maximum": 1},
    },
}

ORACLE_CONTEXT_SCHEMA = {
    "schema_version": "aal.beatoven.oracle_context.v1",
    "type": "object",
    "required": ["kairos_window", "ritual_density", "symbolic_load"],
    "properties": {
        "kairos_window": {"type": "string", "enum": ["open", "closed", "narrowing"]},
        "ritual_density": {"type": "number", "minimum": 0, "maximum": 1},
        "symbolic_load": {"type": "number", "minimum": 0, "maximum": 1},
    },
}
