"""Canonical SourceAtlas registry for deterministic source resolution."""

from __future__ import annotations

from typing import Dict, List, Tuple

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.schema.tvm import TVMVectorId
from abraxas.sources.types import (
    Cadence,
    CachePolicy,
    SourceKind,
    SourceRecord,
    SourceRef,
    SourceSpec,
)

SOURCE_ATLAS_SCHEMA_VERSION = "source_atlas.v0.1"


class SourceAtlas(BaseModel):
    schema_version: str = Field(SOURCE_ATLAS_SCHEMA_VERSION)
    records: List[SourceRecord] = Field(default_factory=list)
    provenance: Dict[str, str] = Field(default_factory=dict)

    def canonical_payload(self) -> Dict[str, object]:
        records = [record.canonical_payload() for record in self.records]
        return {
            "schema_version": self.schema_version,
            "records": records,
            "provenance": self.provenance,
        }

    def atlas_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))


def _records() -> List[SourceSpec]:
    return [
        SourceSpec(
            source_id="NOAA_NCEI_CDO_V2",
            kind=SourceKind.meteorological_climate,
            provider="NOAA NCEI (Climate Data Online)",
            cadence=Cadence.daily,
            backfill="deep_historical",
            tvm_vectors=[
                TVMVectorId.V7_COGNITIVE_LOAD.value,
                TVMVectorId.V8_EMOTIONAL_CLIMATE.value,
                TVMVectorId.V11_ECONOMIC_STRESS.value,
            ],
            mda_domains=["ENVIRONMENT", "ECONOMIC_STRESS"],
            adapter="ncei_cdo_v2",
            cache_policy=CachePolicy.required,
            determinism_notes="cache_required; cache raw responses; hash+timestamp every pull.",
            provenance_notes="Tokened API; cache raw responses; hash+timestamp every pull.",
            refs=[
                SourceRef(
                    id="NCEI_CDO_Web_Services",
                    title="NCEI CDO Web Services",
                    url="https://www.ncei.noaa.gov/cdo-web/webservices/v2",
                ),
                SourceRef(
                    id="CDO_Overview",
                    title="Climate Data Online Overview",
                    url="https://www.ncei.noaa.gov/cdo-web/",
                ),
            ],
        ),
        SourceRecord(
            source_id="NOAA_SWPC_PLANETARY_KP",
            kind=SourceKind.geomagnetic,
            provider="NOAA SWPC",
            cadence=Cadence.hourly,
            backfill="1994_plus_tables",
            tvm_vectors=[
                TVMVectorId.V12_TECHNICAL_CONSTRAINT.value,
                TVMVectorId.V15_RITUAL_COHESION.value,
                TVMVectorId.V13_ARCHETYPAL_ACTIVATION.value,
            ],
            mda_domains=["INFRASTRUCTURE", "SYMBOLIC_COHESION"],
            adapter="swpc_kp_json",
            cache_policy=CachePolicy.required,
            determinism_notes="cache_required; cache raw+parsed packets.",
            provenance_notes="SWPC provides observed Kp JSON; store as raw+parsed packets.",
            refs=[
                SourceRef(
                    id="SWPC_Planetary_K_Index",
                    title="SWPC Planetary K Index",
                    url="https://services.swpc.noaa.gov/json/planetary_k_index_1m.json",
                ),
                SourceRef(
                    id="SWPC_Station_KA_Indices",
                    title="SWPC Station K Indices",
                    url="https://services.swpc.noaa.gov/json/geomag/k_index_1m.json",
                ),
            ],
        ),
        SourceRecord(
            source_id="NASA_JPL_HORIZONS_EPHEM",
            kind=SourceKind.astronomical,
            provider="NASA JPL SSD (Horizons)",
            cadence=Cadence.daily,
            backfill="computed_on_demand",
            tvm_vectors=[
                TVMVectorId.V15_RITUAL_COHESION.value,
                TVMVectorId.V13_ARCHETYPAL_ACTIVATION.value,
            ],
            mda_domains=["TEMPORAL_MECHANICS", "SYMBOLIC_TIMING"],
            adapter="jpl_horizons_api",
            cache_policy=CachePolicy.required,
            determinism_notes="cache_required; API deterministic per params.",
            provenance_notes="API is deterministic given params; cache request+response; hash.",
            refs=[
                SourceRef(
                    id="Horizons_API",
                    title="JPL Horizons API",
                    url="https://ssd.jpl.nasa.gov/api/horizons.api",
                ),
                SourceRef(
                    id="Horizons_Lookup_API",
                    title="JPL Horizons Lookup API",
                    url="https://ssd.jpl.nasa.gov/api/horizons.api",
                ),
            ],
        ),
        SourceRecord(
            source_id="IANA_TZDB",
            kind=SourceKind.timezones,
            provider="IANA (tzdb)",
            cadence=Cadence.on_release,
            backfill="full_history",
            tvm_vectors=[
                TVMVectorId.V3_DISTRIBUTION_DYNAMICS.value,
                TVMVectorId.V15_RITUAL_COHESION.value,
            ],
            mda_domains=["TEMPORAL_SUITE"],
            adapter="tzdb_snapshot",
            cache_policy=CachePolicy.required,
            determinism_notes="vendored_snapshot; version pinned to 2025c.",
            provenance_notes="Vendor tzdb tarball version; record version string (e.g., 2025c).",
            refs=[
                SourceRef(
                    id="IANA_Time_Zone_Database",
                    title="IANA Time Zone Database",
                    url="https://www.iana.org/time-zones",
                )
            ],
        ),
        SourceRecord(
            source_id="UNICODE_CLDR_SUPPLEMENTAL",
            kind=SourceKind.calendars_localization,
            provider="Unicode CLDR",
            cadence=Cadence.on_release,
            backfill="release_history",
            tvm_vectors=[
                TVMVectorId.V15_RITUAL_COHESION.value,
                TVMVectorId.V10_GOVERNANCE_PRESSURE.value,
            ],
            mda_domains=["TEMPORAL_SUITE", "CULTURE"],
            adapter="cldr_snapshot",
            cache_policy=CachePolicy.required,
            determinism_notes="vendored_snapshot; record CLDR version+commit hash.",
            provenance_notes="Vendor CLDR supplemental files; record CLDR version+commit hash.",
            refs=[
                SourceRef(
                    id="CLDR_Supplemental_Data",
                    title="CLDR Supplemental Data",
                    url="https://cldr.unicode.org/index",
                ),
                SourceRef(
                    id="LDML_Supplemental",
                    title="LDML Supplemental",
                    url="https://unicode.org/reports/tr35/tr35-dates.html#Supplemental_Data",
                ),
                SourceRef(
                    id="LDML_Dates_SupplementalCalendarData",
                    title="LDML Supplemental Calendar Data",
                    url="https://unicode.org/reports/tr35/tr35-dates.html#Supplemental_Data",
                ),
            ],
        ),
        SourceRecord(
            source_id="NIST_TIME_BULLETINS",
            kind=SourceKind.time_integrity,
            provider="NIST",
            cadence=Cadence.monthly,
            backfill="1997_plus",
            tvm_vectors=[
                TVMVectorId.V2_SIGNAL_INTEGRITY.value,
                TVMVectorId.V12_TECHNICAL_CONSTRAINT.value,
            ],
            mda_domains=["TEMPORAL_SUITE", "INFRASTRUCTURE"],
            adapter="nist_bulletin_pdf_index",
            cache_policy=CachePolicy.required,
            determinism_notes="cache_required; cache PDF bulletins and parse deterministically.",
            provenance_notes="PDF index; cache bulletins and parse deterministically.",
            refs=[
                SourceRef(
                    id="NIST_Time_Scale_Bulletins",
                    title="NIST Time Scale Bulletins",
                    url="https://www.nist.gov/pml/time-and-frequency-division/time-realization/leap-seconds",
                )
            ],
        ),
        SourceRecord(
            source_id="TOMSK_SOS_SCHUMANN",
            kind=SourceKind.schumann_resonance,
            provider="Tomsk State University (Space Observing System)",
            cadence=Cadence.daily,
            backfill="limited_archive",
            tvm_vectors=[
                TVMVectorId.V8_EMOTIONAL_CLIMATE.value,
                TVMVectorId.V13_ARCHETYPAL_ACTIVATION.value,
                TVMVectorId.V15_RITUAL_COHESION.value,
            ],
            mda_domains=["SYMBOLIC_COHESION", "ENVIRONMENTAL_FIELDS"],
            adapter="tomsk_sos_scrape_cache",
            cache_policy=CachePolicy.required,
            determinism_notes="cache_required; store minimal derived metrics + screenshot hashes.",
            provenance_notes="Site states copyright restrictions; store minimal derived metrics + screenshot hashes.",
            legal_notes="Respect stated restrictions; prefer derived features, not redistribution of raw images.",
            refs=[
                SourceRef(
                    id="Tomsk_SOS_Schumann_Page_Archive",
                    title="Tomsk SOS Schumann Resonance",
                    url="http://sosrff.tsu.ru/new/shumann/",
                )
            ],
        ),
    ]


def build_source_atlas() -> SourceAtlas:
    records = sorted(_records(), key=lambda r: r.source_id)
    payload = [record.canonical_payload() for record in records]
    run_id = f"source_atlas_{sha256_hex(canonical_json(payload))[:12]}"
    provenance = {
        "generated_at_utc": "2026-01-01T00:00:00Z",
        "run_id": run_id,
        "notes": "Canonical SourceAtlas v0.1",
    }
    return SourceAtlas(records=records, provenance=provenance)


def atlas_version() -> str:
    return "0.1"


def list_sources() -> List[SourceSpec]:
    return sorted(_records(), key=lambda r: r.source_id)


def get_source(source_id: str) -> SourceSpec | None:
    for record in list_sources():
        if record.source_id == source_id:
            return record
    return None


def resolve_sources(source_ids: List[str]) -> Tuple[List[SourceRecord], List[str]]:
    atlas = build_source_atlas()
    records = {record.source_id: record for record in atlas.records}
    resolved = []
    missing = []
    for source_id in source_ids:
        record = records.get(source_id)
        if record is None:
            missing.append(source_id)
        else:
            resolved.append(record)
    return resolved, missing
