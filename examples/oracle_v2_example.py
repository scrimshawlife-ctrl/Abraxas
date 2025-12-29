#!/usr/bin/env python3
"""
Oracle v2 Example: Signal → Compression → Forecast → Narrative

Demonstrates the unified Oracle v2 pipeline that integrates:
- Domain Compression Engine (DCE) with lifecycle awareness
- Lifecycle forecasting with phase transitions
- Resonance detection across domains
- Memetic weather trajectory prediction
- Provenance bundles with SHA-256 tracking
"""

from abraxas.oracle.v2 import (
    OracleSignal,
    create_oracle_v2_pipeline,
)
from abraxas.lexicon.dce import (
    DomainCompressionEngine,
    DCERegistry,
    DCEPack,
    DCEEntry,
    LifecycleState,
)


def create_sample_dce() -> DomainCompressionEngine:
    """Create a sample DCE with politics domain lexicon."""
    registry = DCERegistry()

    # Create politics lexicon v1.0
    politics_pack = DCEPack(
        domain="politics",
        version="1.0",
        entries={
            "equality": DCEEntry(
                token="equality",
                weight=0.8,
                lifecycle_state=LifecycleState.FRONT,
                domain="politics",
            ),
            "justice": DCEEntry(
                token="justice",
                weight=0.7,
                lifecycle_state=LifecycleState.FRONT,
                domain="politics",
            ),
            "freedom": DCEEntry(
                token="freedom",
                weight=0.75,
                lifecycle_state=LifecycleState.SATURATED,
                domain="politics",
            ),
            "establishment": DCEEntry(
                token="establishment",
                weight=0.6,
                lifecycle_state=LifecycleState.FRONT,
                domain="politics",
            ),
            "elite": DCEEntry(
                token="elite",
                weight=0.65,
                lifecycle_state=LifecycleState.PROTO,
                domain="politics",
            ),
        },
        lineage=None,
    )

    registry.register(politics_pack)
    return DomainCompressionEngine(registry=registry)


def main():
    """Run Oracle v2 pipeline example."""
    print("=" * 80)
    print("Oracle v2 Pipeline Example")
    print("=" * 80)

    # Create DCE
    print("\n[1/4] Creating Domain Compression Engine...")
    dce = create_sample_dce()
    print("✓ DCE initialized with politics lexicon v1.0")

    # Create Oracle v2 pipeline
    print("\n[2/4] Creating Oracle v2 pipeline...")
    pipeline = create_oracle_v2_pipeline()
    pipeline._dce = dce  # Wire up DCE
    print("✓ Oracle v2 pipeline ready")

    # Create sample signal
    print("\n[3/4] Creating sample oracle signal...")
    signal = OracleSignal(
        domain="politics",
        subdomain="rhetoric",
        observations=[
            "The establishment continues to ignore the people",
            "We need equality and justice for all",
            "Freedom is under threat from the elite",
        ],
        tokens=["establishment", "people", "equality", "justice", "freedom", "elite", "threat"],
        timestamp_utc="2025-12-29T12:00:00Z",
        source_id="sample-source-001",
        meta={"context": "political discourse", "region": "US"},
    )
    print(f"✓ Signal created: {len(signal.tokens)} tokens from {signal.domain} domain")

    # Process through pipeline
    print("\n[4/4] Processing through Oracle v2 pipeline...")
    print("   Phase 1: Compression (DCE → STI/RDV)")
    print("   Phase 2: Forecast (Lifecycle → Resonance → Weather)")
    print("   Phase 3: Narrative (Provenance bundles)")
    print()

    output = pipeline.process(
        signal=signal,
        run_id="EXAMPLE-001",
        git_sha="abc123def456",
    )

    # Display results
    print("\n" + "=" * 80)
    print("ORACLE V2 OUTPUT")
    print("=" * 80)

    print(f"\nRun ID: {output.run_id}")
    print(f"Pipeline Version: {output.pipeline_version}")
    print(f"Created: {output.created_at_utc}")

    print("\n--- COMPRESSION PHASE ---")
    print(f"Domain: {output.compression.domain}")
    print(f"Version: {output.compression.version}")
    print(f"Compressed Tokens: {len(output.compression.compressed_tokens)}")
    for token, weight in sorted(
        output.compression.compressed_tokens.items(), key=lambda x: -x[1]
    ):
        state = output.compression.lifecycle_states.get(token, "unknown")
        print(f"  • {token:20s} weight={weight:.3f} state={state}")

    print(f"\nDomain Signals: {len(output.compression.domain_signals)}")
    for signal_type in output.compression.domain_signals:
        strength = output.compression.signal_strengths.get(signal_type, 0.0)
        print(f"  • {signal_type:30s} strength={strength:.3f}")

    print(f"\nTransparency Score (STI): {output.compression.transparency_score:.3f}")
    print(f"Affect Direction (RDV): {output.compression.affect_direction}")

    print("\n--- FORECAST PHASE ---")
    print(f"Phase Transitions: {len(output.forecast.phase_transitions)}")
    for token, next_state in output.forecast.phase_transitions.items():
        prob = output.forecast.transition_probabilities.get(token, 0.0)
        hours = output.forecast.time_to_transition.get(token, 0.0)
        print(f"  • {token:20s} → {next_state:15s} prob={prob:.3f} eta={hours:.1f}h")

    print(f"\nResonance Score: {output.forecast.resonance_score:.3f}")
    print(f"Resonating Domains: {', '.join(output.forecast.resonating_domains) or 'none'}")

    print(f"\nWeather Trajectory: {output.forecast.weather_trajectory}")
    print(f"Memetic Pressure: {output.forecast.memetic_pressure:.3f}")
    print(f"Drift Velocity: {output.forecast.drift_velocity:+.3f}")

    print("\n--- NARRATIVE PHASE ---")
    print(f"Bundle ID: {output.narrative.bundle_id}")
    print(f"Bundle Hash: {output.narrative.bundle_hash[:16]}...")
    print(f"Confidence Band: {output.narrative.confidence_band}")

    print(f"\nCascade Sheet:")
    for key, value in output.narrative.cascade_sheet.items():
        print(f"  • {key}: {value}")

    if output.narrative.contamination_advisory:
        print(f"\n⚠️  Contamination Advisory:")
        for key, value in output.narrative.contamination_advisory.items():
            print(f"  • {key}: {value}")

    print(f"\nEvidence Trail:")
    print(f"  • Tokens: {len(output.narrative.evidence_tokens)}")
    print(f"  • Signals: {len(output.narrative.evidence_signals)}")
    print(f"  • Transitions: {len(output.narrative.evidence_transitions)}")

    print(f"\nNarrative Summary:")
    print(f"  {output.narrative.narrative_summary}")

    print("\n" + "=" * 80)
    print("✓ Oracle v2 pipeline completed successfully")
    print("=" * 80)


if __name__ == "__main__":
    main()
