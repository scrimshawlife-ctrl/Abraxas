"""Deterministic 2025 seed pack generator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.schema.oracle_seed_pack import SeedPack, SeedPackProvenance, SeedRecord
from abraxas.schema.tvm import TVM_VECTOR_IDS

SEEDPACK_VERSION = "0.1"
SEEDPACK_SCHEMA_VERSION = "seedpack.v0.1"
DEFAULT_GENERATED_AT = "2026-01-01T00:00:00Z"
DEFAULT_SOURCES = [
    "https://www.imf.org/en/Publications/WEO",
    "https://www.worldbank.org/en/publication/global-economic-prospects",
    "https://www.un.org/en/global-issues/climate-change",
    "https://www.weforum.org/reports/global-risks-report-2025/",
    "https://www.bis.org/statistics/",
    "https://www.oecd.org/economic-outlook/",
]
DEFAULT_ASSUMPTIONS = [
    "retroactive_seedpack_v0.1",
    "shadow_only_dataset",
    "non_exclusionary_intake",
]


def _vector_payload(values: Dict[str, float]) -> Dict[str, float]:
    payload = {vid.value: None for vid in TVM_VECTOR_IDS}
    payload.update(values)
    return payload


def _records() -> List[SeedRecord]:
    rows = [
        {
            "date_utc": "2025-01-15",
            "domain": "economics",
            "summary": "Global growth revised lower amid tightening credit conditions.",
            "vectors": _vector_payload(
                {
                    "V1_SIGNAL_DENSITY": 0.62,
                    "V2_SIGNAL_INTEGRITY": 0.74,
                    "V10_GOVERNANCE_PRESSURE": 0.48,
                    "V11_ECONOMIC_STRESS": 0.71,
                    "V12_TECHNICAL_CONSTRAINT": 0.42,
                }
            ),
            "inference_score": 0.78,
            "provenance": {
                "sources": [
                    "https://www.imf.org/en/Publications/WEO",
                    "https://www.worldbank.org/en/publication/global-economic-prospects",
                ],
                "assumptions": ["macro_review_window_2025Q1"],
                "notes": "Inference derived from macro outlook summaries.",
            },
        },
        {
            "date_utc": "2025-03-22",
            "domain": "technology",
            "summary": "AI governance frameworks accelerate with multi-region compliance convergence.",
            "vectors": _vector_payload(
                {
                    "V1_SIGNAL_DENSITY": 0.58,
                    "V3_DISTRIBUTION_DYNAMICS": 0.55,
                    "V4_SEMANTIC_INFLATION": 0.46,
                    "V10_GOVERNANCE_PRESSURE": 0.66,
                    "V12_TECHNICAL_CONSTRAINT": 0.59,
                }
            ),
            "inference_score": 0.74,
            "provenance": {
                "sources": [
                    "https://www.weforum.org/reports/global-risks-report-2025/",
                ],
                "assumptions": ["policy_convergence_observed"],
                "notes": "Inference based on multi-region policy summaries.",
            },
        },
        {
            "date_utc": "2025-05-05",
            "domain": "climate",
            "summary": "Extreme weather narratives intensify with elevated community stress signals.",
            "vectors": _vector_payload(
                {
                    "V1_SIGNAL_DENSITY": 0.64,
                    "V6_NARRATIVE_LOAD": 0.7,
                    "V7_COGNITIVE_LOAD": 0.61,
                    "V8_EMOTIONAL_CLIMATE": 0.73,
                    "V11_ECONOMIC_STRESS": 0.52,
                }
            ),
            "inference_score": 0.7,
            "provenance": {
                "sources": [
                    "https://www.un.org/en/global-issues/climate-change",
                ],
                "assumptions": ["extreme_weather_cycle_Q2"],
                "notes": "Inference derived from climate risk summaries.",
            },
        },
        {
            "date_utc": "2025-07-19",
            "domain": "society",
            "summary": "Public trust topology shifts amid coordinated misinformation campaigns.",
            "vectors": _vector_payload(
                {
                    "V2_SIGNAL_INTEGRITY": 0.51,
                    "V4_SEMANTIC_INFLATION": 0.57,
                    "V8_EMOTIONAL_CLIMATE": 0.69,
                    "V9_TRUST_TOPOLOGY": 0.43,
                    "V13_ARCHETYPAL_ACTIVATION": 0.6,
                }
            ),
            "inference_score": 0.73,
            "provenance": {
                "sources": [
                    "https://www.weforum.org/reports/global-risks-report-2025/",
                ],
                "assumptions": ["trust_surface_review"],
                "notes": "Inference derived from risk signals and trust indicators.",
            },
        },
        {
            "date_utc": "2025-09-08",
            "domain": "finance",
            "summary": "Liquidity stress pockets appear in regional banking networks.",
            "vectors": _vector_payload(
                {
                    "V1_SIGNAL_DENSITY": 0.55,
                    "V2_SIGNAL_INTEGRITY": 0.69,
                    "V9_TRUST_TOPOLOGY": 0.52,
                    "V11_ECONOMIC_STRESS": 0.67,
                    "V12_TECHNICAL_CONSTRAINT": 0.47,
                }
            ),
            "inference_score": 0.76,
            "provenance": {
                "sources": [
                    "https://www.bis.org/statistics/",
                    "https://www.oecd.org/economic-outlook/",
                ],
                "assumptions": ["liquidity_monitoring_cycle"],
                "notes": "Inference derived from financial stability summaries.",
            },
        },
        {
            "date_utc": "2025-11-30",
            "domain": "culture",
            "summary": "Mythic-symbolic motifs surge across creative platforms and ritual cohesion rises.",
            "vectors": _vector_payload(
                {
                    "V5_SLANG_MUTATION": 0.63,
                    "V6_NARRATIVE_LOAD": 0.58,
                    "V13_ARCHETYPAL_ACTIVATION": 0.74,
                    "V14_IDENTITY_PHASE_STATE": 0.61,
                    "V15_RITUAL_COHESION": 0.72,
                }
            ),
            "inference_score": 0.69,
            "provenance": {
                "sources": [
                    "https://www.weforum.org/reports/global-risks-report-2025/",
                ],
                "assumptions": ["symbolic_domain_monitoring"],
                "notes": "Inference derived from culture signal summaries.",
            },
        },
    ]

    records: List[SeedRecord] = []
    for row in rows:
        base = {
            "date_utc": row["date_utc"],
            "domain": row["domain"],
            "summary": row["summary"],
            "vectors": row["vectors"],
            "inference_score": row["inference_score"],
            "provenance": row["provenance"],
        }
        record_id = f"seed_2025_{sha256_hex(canonical_json(base))[:12]}"
        records.append(SeedRecord(record_id=record_id, **base))
    return records


def build_seedpack() -> SeedPack:
    records = _records()
    run_id = f"seedpack_2025_{sha256_hex(canonical_json([r.model_dump() for r in records]))[:12]}"
    provenance = SeedPackProvenance(
        generated_at_utc=DEFAULT_GENERATED_AT,
        sources=DEFAULT_SOURCES,
        assumptions=DEFAULT_ASSUMPTIONS,
        run_id=run_id,
    )
    return SeedPack(year=2025, records=records, provenance=provenance)


def write_seedpack(path: Path) -> Dict[str, Any]:
    pack = build_seedpack()
    payload = pack.canonical_payload()
    payload["seedpack_hash"] = pack.seedpack_hash()
    payload["schema_version"] = SEEDPACK_SCHEMA_VERSION
    payload["seedpack_version"] = SEEDPACK_VERSION

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate deterministic 2025 seed pack.")
    parser.add_argument("--out", required=True, help="Output path for seedpack JSON")
    args = parser.parse_args()

    write_seedpack(Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
