from __future__ import annotations

from typing import Any, Dict, Tuple

from ..io.config import OverlaysConfig, UserConfig


def run_oracle_engine(uc: UserConfig, oc: OverlaysConfig, day: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    # Deterministic stub for plumbing only.
    # Replace with the real engine; keep output shape identical.
    readout = {
        "header": {"date": day, "location": uc.location_label, "headline": "Interface spine online."},
        "vector_mix": {
            "ritual_density": 0.50,
            "meme_velocity": 0.50,
            "nostalgia": 0.50,
            "symbolic_modulator": "Boot sequence",
            "signal_noise": 0.50,
            "drift_charge": 0.25,
            "coherence": 0.75,
            "notes": "This is a stub. Replace with real oracle engine output.",
        },
        "kairos": {
            "axis_of_fate": "Spine before ornament.",
            "framebreaker": "Missing schema breaks the run.",
            "continuum_binder": "One storage, many views.",
            "silent_sovereign": "Ship the smallest true thing.",
        },
        "runic_weather": {
            "active": ["GATE", "NODE"],
            "interpretations": [
                {"rune": "GATE", "short": "Entry conditions; no incomplete runs."},
                {"rune": "NODE", "short": "UI becomes a graph terminal."},
            ],
        },
        "gate_and_trial": [
            "Run `abx init` then `abx oracle-run`.",
            "Confirm files written under ~/.abraxas/ledger/runs/<date>/.",
        ],
        "memetic_futurecast": {"items": []},
        "financials": {
            "macro": ["Stub mode: no market pulls executed."],
            "tickers": [],
            "crypto": [],
            "risk_note": "Stub output. Real market module will supply this.",
        },
    }

    provenance = {
        "day": day,
        "engine": "stub_oracle_engine",
        "tier": uc.tier,
        "admin": uc.admin,
        "overlays_enabled": oc.enabled,
        "note": "Replace stub with real oracle engine; keep schema-gated output.",
    }
    return readout, provenance


def _stub_engine_adapter(inputs: Any) -> Dict[str, Any]:
    # Keep deterministic; no pretending it's real data.
    day = inputs.day
    location = inputs.user.get("location_label", "Unknown")
    return {
        "header": {"date": day, "location": location, "headline": "Stub engine adapter (plumbing OK)."},
        "vector_mix": {
            "ritual_density": 0.50,
            "meme_velocity": 0.50,
            "nostalgia": 0.50,
            "symbolic_modulator": "Bootstrap",
            "signal_noise": 0.50,
            "drift_charge": 0.25,
            "coherence": 0.75,
            "notes": "Replace with Kernel v2.0 engine output.",
        },
        "kairos": {
            "axis_of_fate": "Spine before ornament.",
            "framebreaker": "Schema gates are law.",
            "continuum_binder": "One ledger; many views.",
            "silent_sovereign": "Ship smallest true loop.",
        },
        "runic_weather": {
            "active": ["GATE", "NODE"],
            "interpretations": [
                {"rune": "GATE", "short": "Entry conditions; no incomplete runs."},
                {"rune": "NODE", "short": "UI becomes a graph terminal."},
            ],
        },
        "gate_and_trial": [
            "Run `abx oracle-run` and confirm files written.",
            "Enable overlays only if modules installed.",
        ],
        "memetic_futurecast": {"items": []},
        "financials": {"macro": ["Stub mode."], "tickers": [], "crypto": [], "risk_note": "Stub."},
        "overlays": {"enabled": inputs.overlays_enabled, "tier_ctx": inputs.tier_ctx},
    }
