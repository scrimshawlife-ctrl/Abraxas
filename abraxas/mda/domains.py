"""MDA domain declarations with SourceAtlas bindings."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from abraxas.schema.tvm import TVMVectorId


class MDADomain(BaseModel):
    domain_id: str
    declared_sources: List[str] = Field(default_factory=list)
    declared_vectors_in: List[str] = Field(default_factory=list)
    declared_vectors_out: List[str] = Field(default_factory=list)
    cadence_preferences: List[str] = Field(default_factory=list)


def list_mda_domains() -> List[MDADomain]:
    return [
        MDADomain(
            domain_id="TEMPORAL_SUITE",
            declared_sources=[
                "IANA_TZDB",
                "UNICODE_CLDR_SUPPLEMENTAL",
                "NIST_TIME_BULLETINS",
            ],
            declared_vectors_in=[
                TVMVectorId.V3_DISTRIBUTION_DYNAMICS.value,
                TVMVectorId.V15_RITUAL_COHESION.value,
                TVMVectorId.V2_SIGNAL_INTEGRITY.value,
                TVMVectorId.V12_TECHNICAL_CONSTRAINT.value,
            ],
            cadence_preferences=["on_release", "monthly"],
        ),
        MDADomain(
            domain_id="ENVIRONMENT",
            declared_sources=["NOAA_NCEI_CDO_V2"],
            declared_vectors_in=[
                TVMVectorId.V7_COGNITIVE_LOAD.value,
                TVMVectorId.V8_EMOTIONAL_CLIMATE.value,
                TVMVectorId.V11_ECONOMIC_STRESS.value,
            ],
            cadence_preferences=["daily"],
        ),
        MDADomain(
            domain_id="INFRASTRUCTURE",
            declared_sources=["NOAA_SWPC_PLANETARY_KP", "NIST_TIME_BULLETINS"],
            declared_vectors_in=[
                TVMVectorId.V12_TECHNICAL_CONSTRAINT.value,
                TVMVectorId.V2_SIGNAL_INTEGRITY.value,
            ],
            cadence_preferences=["hourly", "monthly"],
        ),
        MDADomain(
            domain_id="SYMBOLIC_COHESION",
            declared_sources=["NOAA_SWPC_PLANETARY_KP", "TOMSK_SOS_SCHUMANN"],
            declared_vectors_in=[
                TVMVectorId.V15_RITUAL_COHESION.value,
                TVMVectorId.V13_ARCHETYPAL_ACTIVATION.value,
                TVMVectorId.V8_EMOTIONAL_CLIMATE.value,
            ],
            cadence_preferences=["daily", "hourly"],
        ),
        MDADomain(
            domain_id="ENVIRONMENTAL_FIELDS",
            declared_sources=["TOMSK_SOS_SCHUMANN"],
            declared_vectors_in=[
                TVMVectorId.V8_EMOTIONAL_CLIMATE.value,
                TVMVectorId.V13_ARCHETYPAL_ACTIVATION.value,
                TVMVectorId.V15_RITUAL_COHESION.value,
            ],
            cadence_preferences=["daily"],
        ),
        MDADomain(
            domain_id="TEMPORAL_MECHANICS",
            declared_sources=["NASA_JPL_HORIZONS_EPHEM"],
            declared_vectors_in=[
                TVMVectorId.V13_ARCHETYPAL_ACTIVATION.value,
                TVMVectorId.V15_RITUAL_COHESION.value,
            ],
            cadence_preferences=["daily"],
        ),
        MDADomain(
            domain_id="SYMBOLIC_TIMING",
            declared_sources=["NASA_JPL_HORIZONS_EPHEM"],
            declared_vectors_in=[
                TVMVectorId.V13_ARCHETYPAL_ACTIVATION.value,
                TVMVectorId.V15_RITUAL_COHESION.value,
            ],
            cadence_preferences=["daily"],
        ),
    ]


def declared_sources_for_domains(domains: List[MDADomain]) -> List[str]:
    sources = []
    for domain in domains:
        sources.extend(domain.declared_sources)
    return sorted(set(sources))
