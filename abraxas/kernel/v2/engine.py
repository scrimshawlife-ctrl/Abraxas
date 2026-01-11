from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from ...core.oracle_runner import OracleRunInputs
from ...overlays.dispatcher import OVERLAY_REGISTRY, run_overlay_safe
from ...schemas.oracle_readout_v0 import OracleReadoutV0
from ...schemas.overlay_packet_v0 import OverlayPacketV0


def _header(inputs: OracleRunInputs) -> Dict[str, Any]:
    loc = inputs.user.get("location_label", "Unknown")
    return {
        "date": inputs.day,
        "location": loc,
        "headline": "Coherence pays rent. Noise does not.",
        "tier": inputs.tier_ctx.get("tier"),
    }


def _vector_mix(inputs: OracleRunInputs) -> Dict[str, Any]:
    return {
        "ritual_density": 0.62,
        "meme_velocity": 0.71,
        "nostalgia": 0.48,
        "symbolic_modulator": "Kairos-Compression",
        "signal_noise": 0.56,
        "drift_charge": 0.33,
        "coherence": 0.74,
        "pressure": 0.66,
        "tempo": 0.61,
        "attention_frag": 0.52,
        "notes": "BOOTSTRAP: replace with computed values from local ledger + overlays.",
    }


def _kairos(inputs: OracleRunInputs) -> Dict[str, Any]:
    return {
        "axis_of_fate": "Budget time like money. Spend it where feedback is fastest.",
        "framebreaker": "No new complexity unless it reduces applied metrics.",
        "continuum_binder": "One ledger thread: daily oracle → overlays → training ingest.",
        "silent_sovereign": "Write one irreversible artifact today (code, doc, or test).",
    }


def _select_runes(inputs: OracleRunInputs) -> Dict[str, Any]:
    active = ["GATE", "NODE", "FLUX"][:3]
    interpretations = [
        {"rune": "GATE", "short": "Threshold conditions. Start clean; end sealed."},
        {"rune": "NODE", "short": "Interconnect. A UI is a graph of intent."},
        {"rune": "FLUX", "short": "Allow change, but only inside constraints."},
    ]
    return {"active": active[:3], "interpretations": interpretations[:3]}


def _gate_and_trial(inputs: OracleRunInputs) -> List[str]:
    return [
        "Run 1 oracle cycle; confirm deterministic hash invariance for identical inputs.",
        "Ingest 1 training note into KITE (game theory or meteorology).",
        "Write/adjust 1 golden test that enforces non-empty sections even when overlays disabled.",
    ]


def _memetic_futurecast_base(inputs: OracleRunInputs) -> Dict[str, Any]:
    return {
        "schema": "memetic_futurecast.v0",
        "items": [],
        "notes": "Base futurecast empty unless memetic overlay enabled and computable.",
    }


def _financials_base(inputs: OracleRunInputs) -> Dict[str, Any]:
    return {
        "schema": "financials.v0",
        "macro": [],
        "tickers": [],
        "crypto": [],
        "risk_note": "Base financials empty unless financial overlay enabled and computable.",
    }


def _merge_overlays_into_sections(
    base_futurecast: Dict[str, Any],
    base_financials: Dict[str, Any],
    overlay_packets: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    merged = {"schema": "overlays_merge.v0", "applied": [], "warnings": []}

    fc = dict(base_futurecast)
    fin = dict(base_financials)

    def ok_data(name: str) -> Dict[str, Any] | None:
        pkt = overlay_packets.get(name)
        if not pkt:
            return None
        if pkt.get("status") != "ok":
            return None
        return pkt.get("data") or {}

    for name in ("memetic_weather", "semiotic_weather"):
        d = ok_data(name)
        if d and "futurecast_items" in d:
            items = d.get("futurecast_items", [])
            if isinstance(items, list) and items:
                fc_items = fc.get("items", [])
                fc["items"] = list(fc_items) + items
                merged["applied"].append(f"{name}:futurecast_items")

    d = ok_data("financials_plus")
    if d:
        for k in ("macro", "tickers", "crypto", "risk_note"):
            if k in d and d[k]:
                fin[k] = d[k]
                merged["applied"].append(f"financials_plus:{k}")

    a = ok_data("aalmanac")
    if a:
        merged["aalmanac_terms"] = a.get("terms", [])
        merged["applied"].append("aalmanac:terms")

    return fc, fin, merged


def run_oracle_v2(inputs: OracleRunInputs) -> Dict[str, Any]:
    header = _header(inputs)
    vector_mix = _vector_mix(inputs)
    kairos = _kairos(inputs)
    runic_weather = _select_runes(inputs)
    trials = _gate_and_trial(inputs)
    futurecast = _memetic_futurecast_base(inputs)
    financials = _financials_base(inputs)

    ctx = {
        "tier_ctx": inputs.tier_ctx,
        "day": inputs.day,
        "user": inputs.user,
        "checkin": inputs.checkin,
        "limits": inputs.tier_ctx.get("limits", {}),
        "flags": inputs.tier_ctx.get("flags", {}),
        "depth": inputs.tier_ctx.get("depth", {}),
    }

    packets: Dict[str, Dict[str, Any]] = {}
    for name in OVERLAY_REGISTRY.keys():
        enabled = bool(inputs.overlays_enabled.get(name, False))
        pkt: OverlayPacketV0 = run_overlay_safe(name, inputs, ctx, enabled)
        packets[name] = pkt.to_dict()

    futurecast2, financials2, merge_meta = _merge_overlays_into_sections(futurecast, financials, packets)

    provenance = {
        "schema": "oracle_provenance.v0",
        "kernel": "abraxas_kernel.v2.0",
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "note": "Kernel v2 run. Runner adds inputs hash + config context.",
    }

    readout = OracleReadoutV0(
        schema="oracle_readout.v0",
        header=header,
        vector_mix=vector_mix,
        kairos=kairos,
        runic_weather=runic_weather,
        gate_and_trial=trials,
        memetic_futurecast=futurecast2,
        financials=financials2,
        overlays={
            "packets": packets,
            "merge": merge_meta,
        },
        provenance=provenance,
    )
    return readout.to_dict()
