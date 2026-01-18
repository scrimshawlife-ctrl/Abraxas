"""SLANG-HIST.v1 schemas.

Artifact: SLANG-HIST.v1 (Historical Seed Corpus)
Unit: SlangPacket.v1 + SlangMetrics.v1
Metrics: STI, CP, IPS, SDR, NMC, ARF, SDI, IV, CLS, SSF
Method: seed_heuristic_rules.v1
Constraint: observation-only; may observe, never govern
Evidence: none (no frequency series yet)
"""

from __future__ import annotations

from typing import Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

MetricName = Literal["STI", "CP", "IPS", "SDR", "NMC", "ARF", "SDI", "IV", "CLS", "SSF"]


class MetricsMethodV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    method: Literal["seed_heuristic_rules.v1"]
    evidence: str = Field(..., min_length=1)


class SlangMetricsV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ok", "not_computable"] = "ok"
    not_computable_reason: Optional[str] = None

    STI: int = Field(..., ge=0, le=100)
    CP: int = Field(..., ge=0, le=100)
    IPS: int = Field(..., ge=0, le=100)
    SDR: int = Field(..., ge=0, le=100)
    NMC: int = Field(..., ge=0, le=100)
    ARF: int = Field(..., ge=0, le=100)
    SDI: int = Field(..., ge=0, le=100)
    IV: int = Field(..., ge=0, le=100)
    CLS: int = Field(..., ge=0, le=100)
    SSF: int = Field(..., ge=0, le=100)

    method: MetricsMethodV1

    @classmethod
    def not_computable(cls, *, reason: str, method: MetricsMethodV1) -> "SlangMetricsV1":
        return cls(
            status="not_computable",
            not_computable_reason=reason,
            STI=0,
            CP=0,
            IPS=0,
            SDR=0,
            NMC=0,
            ARF=0,
            SDI=0,
            IV=0,
            CLS=0,
            SSF=0,
            method=method,
        )


class SlangProvenanceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str = Field(..., min_length=0)
    collector: str = Field(..., min_length=0)
    notes: str = Field(default="")


class SlangPacketV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    packet_id: str = Field(..., min_length=1)
    term: str = Field(..., min_length=1)
    level: Literal["L1", "L2", "L3", "L4", "L5", "L6"]
    medium: Literal["oral", "print", "broadcast", "internet"]
    velocity: Literal["slow", "fast", "viral"]
    decay_pattern: Literal["fade", "volatile", "flip", "revive", "institutionalize"]
    polarity: Literal["neutral", "ironic", "fluid"]
    taboo_level: Literal["none", "low", "medium", "high"]
    role_type: Literal[
        "role",
        "job",
        "tool",
        "stance",
        "praise",
        "insult",
        "descriptor",
        "interjection",
        "other",
    ]
    moderation_euphemism: bool = False
    suppression_risk: Literal["low", "medium", "high"] = "low"
    observation_lane: Literal["observation_only"] = "observation_only"
    provenance: SlangProvenanceV1
    seed_overrides: Optional[Dict[MetricName, int]] = None
    metrics: Optional[SlangMetricsV1] = None


class SlangHistSeedV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact: Literal["SLANG-HIST.v1"]
    unit: Literal["SlangPacket.v1 + SlangMetrics.v1"]
    method: Literal["seed_heuristic_rules.v1"]
    constraint: Literal["observation-only; may observe, never govern"]
    evidence: Literal["none (no frequency series yet)"]
    packets: list[SlangPacketV1]
    version: str = Field(..., min_length=1)
