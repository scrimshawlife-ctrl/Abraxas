from __future__ import annotations

from typing import Any, Dict


def mda_to_oracle_signal_v2(mda_out: Dict[str, Any]) -> Dict[str, Any]:
    env = mda_out.get("envelope", {}) or {}
    dsp = mda_out.get("dsp", []) or []
    fusion = mda_out.get("fusion_graph", {}) or {}
    aggs = mda_out.get("domain_aggregates", {}) or {}
    shadow = mda_out.get("shadow", None)

    signal = {
        "oracle_signal_v2": {
            "mda_v1_1": {
                "envelope": env,
                "domain_aggregates": aggs,
                "dsp": dsp,
                "fusion": fusion,
            }
        }
    }
    if isinstance(shadow, dict):
        signal["oracle_signal_v2"]["mda_v1_1"]["shadow"] = shadow
    return signal


def shallow_schema_check(signal: Dict[str, Any]) -> None:
    if "oracle_signal_v2" not in signal:
        raise ValueError("signal missing oracle_signal_v2")
    mda = (signal.get("oracle_signal_v2") or {}).get("mda_v1_1")
    if not isinstance(mda, dict):
        raise ValueError("signal missing oracle_signal_v2.mda_v1_1")
    for key in ("envelope", "domain_aggregates", "dsp", "fusion"):
        if key not in mda:
            raise ValueError(f"signal missing oracle_signal_v2.mda_v1_1.{key}")
