import sys
import json
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from abraxas.oracle.v2.pipeline import OracleSignal, OracleV2Pipeline


DST = Path("tests/fixtures/event_correlation/envelopes")
DST.mkdir(parents=True, exist_ok=True)


def main() -> None:
    # Deterministic-ish fixtures: stable signal order + fixed timestamp fields.
    # Note: internal provenance fields may still include generation times; that does not
    # affect event-correlation determinism (which fingerprints only artifact_id + created_at).
    fixed_timestamp = "2026-01-01T00:00:00Z"

    base_obs = [
        {
            "domain": "politics",
            "subdomain": "rhetoric",
            "observations": [
                "Political discourse shifting toward equality and justice",
                "Establishment figures facing increased scrutiny",
            ],
            "tokens": ["equality", "justice", "establishment", "scrutiny"],
        },
        {
            "domain": "technology",
            "subdomain": "ai",
            "observations": [
                "AI safety concerns dominating tech discussions",
                "Innovation accelerating in machine learning",
            ],
            "tokens": ["ai", "safety", "innovation", "machine learning", "breakthrough"],
        },
        {
            "domain": "health",
            "subdomain": "public_health",
            "observations": [
                "Public health initiatives expanding nationwide",
                "Wellness programs gaining traction",
            ],
            "tokens": ["public health", "wellness", "prevention", "initiative"],
        },
    ]

    # Build 10 signals by cycling base observations and adding a stable suffix token
    # so compressed_tokens vary and co-occurrence is non-trivial.
    signals: list[OracleSignal] = []
    for i in range(10):
        spec = base_obs[i % len(base_obs)]
        suffix = f"fixture_{i:02d}"
        signals.append(
            OracleSignal(
                domain=spec["domain"],
                subdomain=spec["subdomain"],
                observations=spec["observations"],
                tokens=[*spec["tokens"], suffix],
                timestamp_utc=fixed_timestamp,
                source_id=f"fixture_{spec['domain']}_{i:02d}",
            )
        )

    pipeline = OracleV2Pipeline()

    # Write env_01..env_10
    for idx, sig in enumerate(signals, 1):
        run_id = f"FIXTURE-EC-{idx:03d}"
        out = pipeline.process(sig, run_id=run_id)
        data = asdict(out)
        # Stabilize created-at so windowing & hashing are stable across regenerations.
        data["created_at_utc"] = fixed_timestamp
        (DST / f"env_{idx:02d}.json").write_text(
            json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()

