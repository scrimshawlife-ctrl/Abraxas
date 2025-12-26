"""Abraxas v1.4 Pipeline Integration CLI.

Workflow:
1. Ingest observations (existing)
2. Update AAlmanac (append annotations, compute τ)
3. Compute Weather + affinities
4. Compute D/M metrics (optional when inputs available)
5. Run SOD modules (emit envelopes)
6. Generate artifacts (delta-only default)
7. Persist snapshot for next run

Flags:
- --v1_4: Enable v1.4 pipeline
- --delta_only: Emit only changed fields (default: true)
- --format json|md|both: Output format (default: both)
- --artifacts <list>: Comma-separated artifact types to generate
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from abraxas.core.provenance import Provenance
from abraxas.core.temporal_tau import TauCalculator, Observation
from abraxas.slang.a_almanac_store import AAlmanacStore
from abraxas.slang.lifecycle import LifecycleState
from abraxas.weather.affinity import compute_all_affinities, get_top_affinity
from abraxas.weather.registry import classify_weather
from abraxas.integrity.dm_metrics import compute_artifact_integrity
from abraxas.integrity.composites import (
    compute_narrative_manipulation,
    compute_network_campaign,
    compute_composite_risk,
)
from abraxas.integrity.payload_taxonomy import classify_payload
from abraxas.sod.models import SODInput
from abraxas.sod.ncp import NarrativeCascadePredictor
from abraxas.sod.cnf import CounterNarrativeForecaster
from abraxas.sod.efte import EpistemicFatigueThresholdEngine
from abraxas.sod.spm import SusceptibilityProfileMapper
from abraxas.sod.rrm import RecoveryReStabilizationModel
from abraxas.artifacts.cascade_sheet import write_cascade_sheet
from abraxas.artifacts.manipulation_surface_map import write_manipulation_surface_map
from abraxas.artifacts.contamination_advisory import write_contamination_advisory
from abraxas.artifacts.trust_drift_graph_data import write_trust_drift_graph_data
from abraxas.artifacts.oracle_delta_ledger import write_oracle_delta_ledger


def run_v1_4_pipeline(
    *,
    observations_file: Optional[str] = None,
    delta_only: bool = True,
    output_format: str = "both",
    artifacts: List[str] = None,
    output_dir: str = "data/runs/v1_4",
    run_id: Optional[str] = None,
) -> dict:
    """
    Run complete v1.4 pipeline.

    Args:
        observations_file: Path to observations JSON file (optional)
        delta_only: Emit only changed fields (default: True)
        output_format: Output format ('json', 'md', or 'both')
        artifacts: List of artifact types to generate
        output_dir: Output directory for artifacts
        run_id: Optional run identifier

    Returns:
        Summary dict with run statistics
    """
    run_id = run_id or f"v1.4-{uuid4().hex[:8]}"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"[v1.4] Starting pipeline run: {run_id}")
    print(f"[v1.4] Output directory: {output_path}")

    # Initialize components
    almanac = AAlmanacStore()
    tau_calculator = TauCalculator()
    ncp = NarrativeCascadePredictor(top_k=5)
    cnf = CounterNarrativeForecaster()
    efte = EpistemicFatigueThresholdEngine()
    spm = SusceptibilityProfileMapper()
    rrm = RecoveryReStabilizationModel()

    # 1. Load observations (if provided)
    observations = []
    if observations_file:
        print(f"[v1.4] Loading observations from {observations_file}")
        with open(observations_file, "r", encoding="utf-8") as f:
            obs_data = json.load(f)
            for item in obs_data:
                observations.append(
                    Observation(
                        ts=item["timestamp"],
                        value=item.get("value", 1.0),
                        source_id=item.get("source_id", "unknown"),
                    )
                )
        print(f"[v1.4] Loaded {len(observations)} observations")

    # 2. Update AAlmanac
    print("[v1.4] Updating AAlmanac...")
    current_time_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # For demo: create or update a sample entry
    prov = Provenance(
        run_id=run_id,
        started_at_utc=current_time_utc,
        inputs_hash="demo",
        config_hash="demo",
    )

    term_id = almanac.create_entry_if_missing(
        term="test_term_v1_4",
        class_id="eggcorn",
        created_at=current_time_utc,
        provenance=prov,
    )

    # Append observations as annotations
    for obs in observations[:5]:  # Limit to 5 for demo
        almanac.append_annotation(
            term_id=term_id,
            annotation_type="observation",
            data={"value": obs.value, "source_id": obs.source_id},
            provenance=prov,
        )

    # Compute current state
    state_result = almanac.compute_current_state(
        term_id, run_id=run_id, current_time_utc=current_time_utc
    )
    if state_result:
        lifecycle_state, tau_snapshot = state_result
        print(f"[v1.4] Lifecycle state: {lifecycle_state.value}")
        print(f"[v1.4] τₕ={tau_snapshot.tau_half_life:.2f}h, τᵥ={tau_snapshot.tau_velocity:.2f}")
    else:
        print("[v1.4] No state computed")
        return {"status": "error", "message": "Failed to compute state"}

    # 3. Compute Weather + affinities
    print("[v1.4] Computing weather and affinities...")
    weather_types = classify_weather(tau_snapshot.tau_velocity, tau_snapshot.tau_half_life)
    print(f"[v1.4] Detected weather types: {[w.value for w in weather_types]}")

    tone_flags = ["humor", "irony"]  # Demo tone flags
    top_affinity = get_top_affinity("eggcorn", tau_snapshot, tone_flags)
    print(f"[v1.4] Top affinity: {top_affinity.weather_type} ({top_affinity.total:.2f})")

    # 4. Compute D/M metrics (optional, demo with minimal inputs)
    print("[v1.4] Computing D/M metrics...")
    artifact_integrity = compute_artifact_integrity(
        has_timestamp=True,
        has_source_id=True,
        has_author=False,
        has_provenance_hash=True,
        source_chain_length=2,
    )
    narrative_manipulation = compute_narrative_manipulation(
        framing_indicators=1,
        total_framing_checked=5,
        emotional_word_count=10,
        total_word_count=100,
    )
    network_campaign = compute_network_campaign(
        uniformity_score=0.4,
        propagation_rate=5.0,
        burst_amplitude=2.0,
        domain_count=2,
    )
    risk_indices = compute_composite_risk(
        artifact_integrity, narrative_manipulation, network_campaign
    )
    payload_classification = classify_payload(risk_indices)

    print(f"[v1.4] IRI={risk_indices.iri:.1f}, MRI={risk_indices.mri:.1f}")
    print(f"[v1.4] Payload type: {payload_classification.payload_type.value}")

    # 5. Run SOD modules
    print("[v1.4] Running SOD modules...")
    sod_input = SODInput(
        tau_snapshot=tau_snapshot,
        risk_indices=risk_indices,
        affinity_score=top_affinity,
        context={},
    )

    scenario_envelope = ncp.predict(sod_input, run_id=run_id)
    print(f"[v1.4] NCP generated {len(scenario_envelope.paths)} cascade paths")

    counter_strategies = cnf.forecast(scenario_envelope)
    print(f"[v1.4] CNF generated {len(counter_strategies)} counter-strategies")

    # 6. Generate artifacts
    print("[v1.4] Generating artifacts...")
    artifact_types = artifacts or ["cascade_sheet", "contamination_advisory"]

    formats = ["json", "md"] if output_format == "both" else [output_format]

    for artifact_type in artifact_types:
        for fmt in formats:
            ext = "json" if fmt == "json" else "md"
            artifact_path = output_path / f"{artifact_type}.{ext}"

            if artifact_type == "cascade_sheet":
                write_cascade_sheet(scenario_envelope, prov, str(artifact_path), fmt)
                print(f"[v1.4] Generated {artifact_path}")

            elif artifact_type == "contamination_advisory":
                # Check if any high-risk items
                high_risk = []
                if risk_indices.iri > 70 or risk_indices.mri > 80:
                    high_risk.append((term_id, "test_term_v1_4", risk_indices, payload_classification))
                if high_risk:
                    write_contamination_advisory(high_risk, prov, str(artifact_path), fmt)
                    print(f"[v1.4] Generated {artifact_path}")

    # 7. Persist snapshot
    snapshot_path = output_path / "last_snapshot.json"
    snapshot = {
        "run_id": run_id,
        "timestamp": current_time_utc,
        "tau_snapshot": {
            "tau_half_life": tau_snapshot.tau_half_life,
            "tau_velocity": tau_snapshot.tau_velocity,
            "tau_phase_proximity": tau_snapshot.tau_phase_proximity,
        },
        "risk_indices": {
            "iri": risk_indices.iri,
            "mri": risk_indices.mri,
        },
        "lifecycle_state": lifecycle_state.value,
    }

    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    print(f"[v1.4] Persisted snapshot to {snapshot_path}")

    print(f"[v1.4] Pipeline run complete: {run_id}")

    return {
        "status": "success",
        "run_id": run_id,
        "outputs": list(output_path.glob("*")),
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Abraxas v1.4 Pipeline")
    parser.add_argument(
        "--observations",
        type=str,
        help="Path to observations JSON file",
    )
    parser.add_argument(
        "--delta-only",
        action="store_true",
        default=True,
        help="Emit only changed fields (default: true)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "md", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--artifacts",
        type=str,
        help="Comma-separated list of artifact types to generate",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/runs/v1_4",
        help="Output directory (default: data/runs/v1_4)",
    )

    args = parser.parse_args()

    artifact_list = None
    if args.artifacts:
        artifact_list = [a.strip() for a in args.artifacts.split(",")]

    result = run_v1_4_pipeline(
        observations_file=args.observations,
        delta_only=args.delta_only,
        output_format=args.format,
        artifacts=artifact_list,
        output_dir=args.output_dir,
    )

    if result["status"] == "success":
        print(f"\nSuccess! Run ID: {result['run_id']}")
        sys.exit(0)
    else:
        print(f"\nError: {result.get('message', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
