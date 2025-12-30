#!/usr/bin/env python3
"""Generate sample Oracle v2 outputs as JSONL for testing Weather Bridge CLI.

This script runs the Oracle v2 pipeline with sample data and saves outputs to JSONL.
"""

import json
from dataclasses import asdict
from pathlib import Path

from abraxas.lexicon.dce import (
    DomainCompressionEngine,
    DCERegistry,
    DCEPack,
    DCEEntry,
    LifecycleState,
    LexiconLineage,
)
from abraxas.lexicon.engine import InMemoryLexiconRegistry
from abraxas.oracle.v2.pipeline import OracleV2Pipeline, OracleSignal


def create_sample_dce() -> DomainCompressionEngine:
    """Create a sample DCE with politics lexicon."""
    base_registry = InMemoryLexiconRegistry()
    registry = DCERegistry(base_registry)

    # Create politics lexicon v1.0
    politics_pack = DCEPack(
        domain="politics",
        version="1.0",
        entries=(
            DCEEntry(
                token="equality",
                weight=0.8,
                lifecycle_state=LifecycleState.FRONT,
                domain="politics",
            ),
            DCEEntry(
                token="justice",
                weight=0.7,
                lifecycle_state=LifecycleState.FRONT,
                domain="politics",
            ),
            DCEEntry(
                token="freedom",
                weight=0.75,
                lifecycle_state=LifecycleState.SATURATED,
                domain="politics",
            ),
            DCEEntry(
                token="establishment",
                weight=0.6,
                lifecycle_state=LifecycleState.FRONT,
                domain="politics",
            ),
            DCEEntry(
                token="elite",
                weight=0.65,
                lifecycle_state=LifecycleState.PROTO,
                domain="politics",
            ),
        ),
        lineage=LexiconLineage(
            version="1.0",
            parent_version=None,
        ),
    )

    registry.register(politics_pack)
    return DomainCompressionEngine(registry)


def generate_sample_signals():
    """Generate sample signals for different domains."""
    return [
        OracleSignal(
            domain="politics",
            subdomain="rhetoric",
            observations=[
                "The establishment ignores the people",
                "We need equality and justice for all",
                "Freedom is under threat from elites",
            ],
            tokens=["establishment", "people", "equality", "justice", "freedom", "elite"],
            timestamp_utc="2025-12-29T12:00:00Z",
            source_id="sample_001",
        ),
        OracleSignal(
            domain="politics",
            subdomain="policy",
            observations=[
                "Justice reform is gaining momentum",
                "Equality initiatives expanding nationwide",
            ],
            tokens=["justice", "equality", "reform", "initiative"],
            timestamp_utc="2025-12-29T13:00:00Z",
            source_id="sample_002",
        ),
        OracleSignal(
            domain="politics",
            subdomain="movement",
            observations=[
                "Grassroots movements challenging the establishment",
                "Elite institutions facing scrutiny",
            ],
            tokens=["grassroots", "establishment", "elite", "scrutiny"],
            timestamp_utc="2025-12-29T14:00:00Z",
            source_id="sample_003",
        ),
    ]


def main():
    """Generate sample Oracle outputs and save to JSONL."""
    output_path = Path("data/oracle_runs_sample.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("Generating Sample Oracle v2 Outputs")
    print("=" * 80)

    # Create DCE
    print("\n[1/3] Creating Domain Compression Engine...")
    dce = create_sample_dce()
    print("✓ DCE initialized with politics lexicon v1.0")

    # Create Oracle pipeline
    print("\n[2/3] Creating Oracle v2 pipeline...")
    pipeline = OracleV2Pipeline(dce_engine=dce)
    print("✓ Oracle v2 pipeline ready")

    # Generate signals
    print("\n[3/3] Processing signals and generating outputs...")
    signals = generate_sample_signals()

    outputs = []
    for idx, signal in enumerate(signals, 1):
        run_id = f"SAMPLE-{idx:03d}"
        print(f"\n  Processing signal {idx}/{len(signals)}: {run_id}")
        output = pipeline.process(signal, run_id=run_id, git_sha="abc123")
        outputs.append(output)
        print(f"  ✓ {run_id}: {len(output.compression.compressed_tokens)} tokens, "
              f"{len(output.forecast.phase_transitions)} transitions")

    # Write to JSONL
    print(f"\nWriting {len(outputs)} outputs to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        for output in outputs:
            # Convert to dict using asdict
            output_dict = asdict(output)
            f.write(json.dumps(output_dict, ensure_ascii=False) + "\n")

    print(f"✓ Outputs written to {output_path}")
    print(f"\nFile size: {output_path.stat().st_size:,} bytes")
    print(f"Line count: {len(outputs)}")

    print("\n" + "=" * 80)
    print("Sample Oracle v2 outputs generated successfully!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Test Weather Bridge CLI:")
    print(f"     python -m abraxas.cli.weather_bridge_cli \\")
    print(f"         --oracle-runs {output_path} \\")
    print(f"         --output data/intel/")
    print("\n  2. View generated intel artifacts in data/intel/")
    print("\n  3. Generate weather report:")
    print(f"     python -m abraxas.cli.weather_bridge_cli \\")
    print(f"         --oracle-runs {output_path} \\")
    print(f"         --mode report \\")
    print(f"         --report-path out/reports/weather_report.json")


if __name__ == "__main__":
    main()
