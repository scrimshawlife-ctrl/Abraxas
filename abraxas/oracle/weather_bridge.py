"""Oracle v2 → Weather Intel Bridge

Converts Oracle v2 outputs into intel artifacts for memetic weather system.

Architecture:
- Oracle v2 produces: CompressionPhase, ForecastPhase, NarrativePhase
- Weather system consumes: symbolic_pressure.json, trust_index.json, semantic_drift_signal.json
- This bridge translates between the two formats
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

from abraxas.oracle.v2.pipeline import OracleV2Output


def oracle_to_weather_intel(
    oracle_outputs: List[OracleV2Output],
    output_dir: Path,
) -> Dict[str, Path]:
    """Convert Oracle v2 outputs to weather intel artifacts.

    Args:
        oracle_outputs: List of Oracle v2 outputs (one per domain/run)
        output_dir: Directory to write intel artifacts (e.g., data/intel/)

    Returns:
        Dict mapping intel_type → file_path
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Aggregate data by domain (use domain as rune_id for weather system)
    pressure_data: Dict[str, Any] = {}
    trust_data: Dict[str, Any] = {}
    drift_data: Dict[str, Any] = {}

    for oracle_output in oracle_outputs:
        domain = oracle_output.compression.domain
        rune_id = f"domain_{domain}"  # Weather system uses rune_id

        # Symbolic pressure = memetic_pressure from forecast
        pressure_data[rune_id] = {
            "pressure_score": oracle_output.forecast.memetic_pressure,
            "domain": domain,
            "version": oracle_output.compression.version,
        }

        # Trust index = transparency_score (STI) from compression
        # STI is a trust proxy: higher transparency = higher trust
        trust_data[rune_id] = {
            "trust_index": oracle_output.compression.transparency_score,
            "domain": domain,
            "version": oracle_output.compression.version,
        }

        # Drift signal = drift_velocity from forecast
        # Positive drift = semantic drift, negative = semantic convergence
        drift_flag = abs(oracle_output.forecast.drift_velocity) > 0.2  # Threshold for drift
        drift_data[rune_id] = {
            "drift_flag": drift_flag,
            "drift_velocity": oracle_output.forecast.drift_velocity,
            "domain": domain,
            "version": oracle_output.compression.version,
        }

    # Write intel artifacts
    written = {}

    pressure_path = output_dir / "symbolic_pressure.json"
    pressure_path.write_text(json.dumps(pressure_data, indent=2, sort_keys=True), encoding="utf-8")
    written["symbolic_pressure"] = pressure_path

    trust_path = output_dir / "trust_index.json"
    trust_path.write_text(json.dumps(trust_data, indent=2, sort_keys=True), encoding="utf-8")
    written["trust_index"] = trust_path

    drift_path = output_dir / "semantic_drift_signal.json"
    drift_path.write_text(json.dumps(drift_data, indent=2, sort_keys=True), encoding="utf-8")
    written["semantic_drift"] = drift_path

    return written


def oracle_to_mimetic_weather_fronts(
    oracle_outputs: List[OracleV2Output],
) -> List[Dict[str, Any]]:
    """Convert Oracle v2 phase transitions to mimetic weather fronts.

    Args:
        oracle_outputs: List of Oracle v2 outputs

    Returns:
        List of weather fronts compatible with weather_to_tasks.py
    """
    fronts: List[Dict[str, Any]] = []

    for oracle_output in oracle_outputs:
        domain = oracle_output.compression.domain
        transitions = oracle_output.forecast.phase_transitions

        # Classify transitions into weather fronts
        proto_terms = [tok for tok, state in transitions.items() if state == "Proto"]
        front_terms = [tok for tok, state in transitions.items() if state == "Front"]
        saturated_terms = [tok for tok, state in transitions.items() if state == "Saturated"]
        dormant_terms = [tok for tok, state in transitions.items() if state == "Dormant"]

        # NEWBORN front: New proto terms emerging
        if proto_terms:
            fronts.append({
                "front": "NEWBORN",
                "domain": domain,
                "terms": proto_terms[:10],  # Limit to 10 terms
                "signal": "emergence",
            })

        # MIGRATION front: Proto → Front transitions (active spread)
        if front_terms:
            fronts.append({
                "front": "MIGRATION",
                "domain": domain,
                "terms": front_terms[:10],
                "signal": "compression_accelerating",
            })

        # AMPLIFY front: Front → Saturated (reaching saturation)
        if saturated_terms:
            fronts.append({
                "front": "AMPLIFY",
                "domain": domain,
                "terms": saturated_terms[:10],
                "signal": "saturation",
            })

        # DRIFT front: Any → Dormant (declining terms)
        if dormant_terms:
            fronts.append({
                "front": "DRIFT",
                "domain": domain,
                "terms": dormant_terms[:10],
                "signal": "drift_declining",
            })

        # POLLUTION front: High memetic pressure + negative affect
        if (
            oracle_output.forecast.memetic_pressure > 0.7
            and oracle_output.compression.affect_direction == "negative"
        ):
            # Extract all compressed tokens for pollution front
            pollution_terms = list(oracle_output.compression.compressed_tokens.keys())[:10]
            if pollution_terms:
                fronts.append({
                    "front": "POLLUTION",
                    "domain": domain,
                    "terms": pollution_terms,
                    "signal": "contamination_risk",
                    "memetic_pressure": oracle_output.forecast.memetic_pressure,
                })

    return fronts


def write_mimetic_weather_report(
    oracle_outputs: List[OracleV2Output],
    output_path: Path,
) -> Path:
    """Write complete mimetic weather report from Oracle v2 outputs.

    Args:
        oracle_outputs: List of Oracle v2 outputs
        output_path: Path to write weather report JSON

    Returns:
        Path to written report
    """
    fronts = oracle_to_mimetic_weather_fronts(oracle_outputs)

    report = {
        "version": "oracle_v2_weather_bridge",
        "generated_at_utc": oracle_outputs[0].created_at_utc if oracle_outputs else "",
        "domains_analyzed": len(oracle_outputs),
        "fronts": fronts,
        "summary": {
            "total_fronts": len(fronts),
            "front_types": list({f["front"] for f in fronts}),
        },
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    return output_path
