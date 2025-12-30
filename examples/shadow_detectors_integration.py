"""Shadow Detectors Integration Example

Demonstrates how to use Shadow Detectors v0.1 with ABX-Runes ϟ₇ (SSO).

This example shows:
1. Computing all detectors via registry
2. Serializing results for shadow metrics
3. Feeding detectors to shadow metrics (SCG, FVC, NOR, PTS, CLIP, SEI)
4. Handling not_computable status
"""

from __future__ import annotations

from typing import Any

from abraxas.detectors.shadow.registry import (
    compute_all_detectors,
    list_detectors,
    serialize_detector_results,
)
from abraxas.detectors.shadow.types import DetectorStatus
from abraxas.shadow_metrics import clip, fvc, nor, pts, scg, sei


def example_basic_usage():
    """Basic usage: compute all detectors and serialize."""
    print("=== Basic Usage ===\n")

    # Sample context with detector inputs
    context = {
        # Compliance vs Remix inputs
        "drift": {"drift_score": 0.7, "similarity_early_late": 0.3},
        "lifecycle_state": "Proto",
        "tau": {"tau_velocity": 0.8, "tau_half_life": 12.0, "observation_count": 10},
        "appearances": 5,
        "csp": {"FF": 0.4, "MIO": 0.3},
        "weather_types": ["MW-03"],
        # Meta-Awareness inputs
        "text": "This looks like a manufactured psyop. The algorithm is pushing ragebait again.",
        "dmx": {"overall_manipulation_risk": 0.65, "bucket": "HIGH"},
        "rdv": {"irony": 0.4, "humor": 0.3, "nihilism": 0.2},
        # Negative Space inputs (requires history)
        "symbol_pool": [
            {"narrative_id": "topic_A", "source": "source1"},
            {"narrative_id": "topic_B", "source": "source1"},
        ],
    }

    # History for Negative Space detector
    history = [
        {
            "symbol_pool": [
                {"narrative_id": "topic_A", "source": "source1"},
                {"narrative_id": "topic_B", "source": "source2"},
                {"narrative_id": "topic_C", "source": "source3"},
            ]
        },
        {
            "symbol_pool": [
                {"narrative_id": "topic_A", "source": "source1"},
                {"narrative_id": "topic_B", "source": "source2"},
                {"narrative_id": "topic_C", "source": "source3"},
            ]
        },
        {
            "symbol_pool": [
                {"narrative_id": "topic_A", "source": "source1"},
                {"narrative_id": "topic_C", "source": "source3"},
            ]
        },
    ]

    # Compute all detectors
    results = compute_all_detectors(context, history)

    # Display results
    for detector_id, detector_value in results.items():
        print(f"\n{detector_id}:")
        print(f"  Status: {detector_value.status}")
        if detector_value.status == DetectorStatus.OK:
            print(f"  Value: {detector_value.value:.3f}")
            print(f"  Subscores:")
            for name, score in detector_value.subscores.items():
                print(f"    {name}: {score:.3f}")
        else:
            print(f"  Missing keys: {detector_value.missing_keys}")

    # Serialize for transmission/storage
    serialized = serialize_detector_results(results)
    print(f"\n\nSerialized (deterministic): {len(serialized)} detectors")

    return serialized


def example_shadow_metrics_integration(detector_results: dict[str, Any]):
    """Demonstrate integration with shadow metrics."""
    print("\n\n=== Shadow Metrics Integration ===\n")

    # Add detector results to context
    context = {
        "symbol_pool": [
            {
                "exposed_count": 100,
                "transmission_count": 30,
                "sentiment": "positive",
                "text": "Example text",
                "narrative_id": "topic_A",
                "source": "source1",
            },
            {
                "exposed_count": 150,
                "transmission_count": 45,
                "sentiment": "negative",
                "text": "More content",
                "narrative_id": "topic_B",
                "source": "source2",
            },
        ],
        "time_window_hours": 24,
        # CRITICAL: Add detector results as shadow evidence
        "shadow_detectors": detector_results,
    }

    # Compute SCG with detector evidence
    print("Computing SCG (Social Contagion Gradient)...")
    scg_inputs = scg.extract_inputs(context)
    scg_value, scg_metadata = scg.compute(scg_inputs, scg.get_default_config())
    print(f"  SCG value: {scg_value:.3f}")
    print(f"  R_effective: {scg_metadata['r_effective']:.3f}")
    if "shadow_detector_evidence" in scg_metadata:
        print(f"  ✓ Detector evidence included (shadow-only)")
        print(f"    Detectors: {list(scg_metadata['shadow_detector_evidence'].keys())}")

    # Compute FVC with detector evidence
    print("\nComputing FVC (Filter Velocity Coefficient)...")
    fvc_inputs = fvc.extract_inputs(context)
    fvc_value, fvc_metadata = fvc.compute(fvc_inputs, fvc.get_default_config())
    print(f"  FVC value: {fvc_value:.3f}")
    print(f"  Diversity index: {fvc_metadata['diversity_index']:.3f}")
    if "shadow_detector_evidence" in fvc_metadata:
        print(f"  ✓ Detector evidence included (shadow-only)")

    # Compute NOR with detector evidence
    print("\nComputing NOR (Narrative Overload Rating)...")
    nor_inputs = nor.extract_inputs(context)
    nor_value, nor_metadata = nor.compute(nor_inputs, nor.get_default_config())
    print(f"  NOR value: {nor_value:.3f}")
    print(f"  Narrative count: {nor_metadata['narrative_count']}")
    if "shadow_detector_evidence" in nor_metadata:
        print(f"  ✓ Detector evidence included (shadow-only)")

    # Compute SEI with detector evidence
    print("\nComputing SEI (Sentiment Entropy Index)...")
    sei_inputs = sei.extract_inputs(context)
    sei_value, sei_metadata = sei.compute(sei_inputs, sei.get_default_config())
    print(f"  SEI value: {sei_value:.3f}")
    print(f"  Entropy: {sei_metadata['entropy_raw']:.3f}")
    if "shadow_detector_evidence" in sei_metadata:
        print(f"  ✓ Detector evidence included (shadow-only)")

    print("\n✅ All shadow metrics computed with detector evidence")
    print("   Detector results are in metadata only - NO influence on values")


def example_not_computable_handling():
    """Demonstrate handling of not_computable status."""
    print("\n\n=== Handling not_computable ===\n")

    # Context with missing required inputs
    incomplete_context = {
        "text": "Some text",  # Meta-awareness has text
        # Missing: drift, lifecycle_state, tau (compliance_remix)
        # Missing: sufficient history (negative_space)
    }

    results = compute_all_detectors(incomplete_context, history=None)

    print("Detector statuses with incomplete inputs:\n")
    for detector_id, detector_value in results.items():
        status_symbol = "✓" if detector_value.status == DetectorStatus.OK else "✗"
        print(f"{status_symbol} {detector_id}: {detector_value.status}")
        if detector_value.status == DetectorStatus.NOT_COMPUTABLE:
            print(f"  Missing: {', '.join(detector_value.missing_keys)}")

    print("\nℹ️  Shadow metrics depending on not_computable detectors")
    print("   should also return not_computable for affected computations")


def example_registry_inspection():
    """Demonstrate registry inspection capabilities."""
    print("\n\n=== Registry Inspection ===\n")

    detectors = list_detectors()

    print(f"Registered detectors: {len(detectors)}\n")
    for detector_def in detectors:
        print(f"{detector_def.detector_id.value}:")
        print(f"  Name: {detector_def.name}")
        print(f"  Version: {detector_def.version}")
        print(f"  Mode: {detector_def.mode}")
        print(f"  No Influence: {detector_def.no_influence}")
        print(f"  Governance: {detector_def.governance}")
        print(f"  Required inputs: {', '.join(detector_def.required_inputs)}")
        print(f"  Optional inputs: {len(detector_def.optional_inputs)} fields")
        print()


def example_abx_runes_pattern():
    """Demonstrate the ABX-Runes ϟ₇ (SSO) access pattern."""
    print("\n\n=== ABX-Runes ϟ₇ (SSO) Pattern ===\n")

    print("CRITICAL: Shadow detectors MUST be invoked via ABX-Runes ϟ₇ (SSO) only.")
    print("Direct invocation is FORBIDDEN.\n")

    print("Correct pattern:")
    print("```python")
    print("# Via ABX-Runes ϟ₇ operator (Shadow Structural Observer)")
    print("from abraxas.runes.operators.sso import apply_sso")
    print("")
    print("# SSO applies isolation and computes detectors")
    print("context = apply_sso(symbol_pool)")
    print("")
    print("# context['shadow_detectors'] now contains:")
    print("# - All detector results")
    print("# - Isolation proof")
    print("# - Audit log")
    print("```\n")

    print("The SSO rune ensures:")
    print("  ✓ Access control enforcement")
    print("  ✓ Isolation from decision-making")
    print("  ✓ Audit trail generation")
    print("  ✓ no_influence_guarantee validation")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Shadow Detectors v0.1 Integration Examples")
    print("=" * 60)

    # 1. Basic usage
    detector_results = example_basic_usage()

    # 2. Shadow metrics integration
    example_shadow_metrics_integration(detector_results)

    # 3. not_computable handling
    example_not_computable_handling()

    # 4. Registry inspection
    example_registry_inspection()

    # 5. ABX-Runes pattern
    example_abx_runes_pattern()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
