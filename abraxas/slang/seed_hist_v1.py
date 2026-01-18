"""SLANG-HIST.v1 seed corpus loader + heuristic scorer.

Artifact: SLANG-HIST.v1 (Historical Seed Corpus)
Unit: SlangPacket.v1 + SlangMetrics.v1
Metrics: STI, CP, IPS, SDR, NMC, ARF, SDI, IV, CLS, SSF
Method: seed_heuristic_rules.v1
Constraint: observation-only; may observe, never govern
Evidence: none (no frequency series yet)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping

import json

from pydantic import ValidationError

from abraxas.mda.types import stable_json_dumps
from abraxas.schemas.slang_hist_v1 import (
    MetricsMethodV1,
    MetricName,
    SlangHistSeedV1,
    SlangMetricsV1,
    SlangPacketV1,
)

SEED_METHOD = MetricsMethodV1(
    method="seed_heuristic_rules.v1",
    evidence="none (no frequency series yet)",
)

ARF_MAP = {"slow": 30, "fast": 65, "viral": 90}
SDI_MAP = {
    "fade": 70,
    "volatile": 85,
    "flip": 75,
    "revive": 55,
    "institutionalize": 20,
}
NMC_MAP = {"oral": 10, "print": 20, "broadcast": 40, "internet": 80}

STI_BY_LEVEL = {"L1": 45, "L2": 50, "L3": 60, "L4": 65, "L5": 70, "L6": 75}
ROLE_CP_HIGH = {"role", "job", "tool", "stance"}

CLS_BY_DECAY = {
    "institutionalize": 85,
    "revive": 60,
    "fade": 25,
    "volatile": 40,
    "flip": 55,
}


def _seed_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "slang" / "slang_hist_seed_v1.json"


def _clamp(metric: int) -> int:
    return max(0, min(100, int(metric)))


def _base_metrics(packet: SlangPacketV1) -> Dict[MetricName, int]:
    """
    Seed heuristic rules (explicit, deterministic):
      - ARF: slow=30, fast=65, viral=90
      - SDI: fade=70, volatile=85, flip=75, revive=55, institutionalize=20
      - NMC: oral=10, print=20, broadcast=40, internet=80
      - SSF baseline:
          * oral/print/broadcast: 5–15 (default 5)
          * internet: 10–35 (default 10)
          * moderation/euphemism pattern: 85–95 (unalive=95)
      - CLS guidance:
          * institutionalize: 80–95
          * revive: 55–70
          * fade: 15–35
          * volatile: 25–55
      - IPS/IV:
          * boost when polarity in {ironic, fluid} and/or decay_pattern=flip
          * taboo_level boosts moderately
      - CP:
          * role/job/tool/stance terms score higher (70–90)
          * generic praise/insult lower (30–55)
    """
    arf = ARF_MAP[packet.velocity]
    sdi = SDI_MAP[packet.decay_pattern]
    nmc = NMC_MAP[packet.medium]

    ssf_base = 10 if packet.medium == "internet" else 5
    if packet.moderation_euphemism:
        ssf = 95
    else:
        if packet.suppression_risk == "medium":
            ssf = ssf_base + 5
        elif packet.suppression_risk == "high":
            ssf = ssf_base + 10
        else:
            ssf = ssf_base

    sti = STI_BY_LEVEL[packet.level]
    if packet.polarity in {"ironic", "fluid"}:
        sti += 5
    if packet.role_type in ROLE_CP_HIGH:
        sti += 5
    if packet.decay_pattern == "flip":
        sti += 5

    cp = 80 if packet.role_type in ROLE_CP_HIGH else 50
    if packet.taboo_level in {"medium", "high"}:
        cp += 5
    if packet.medium == "internet":
        cp += 5

    ips = 20
    iv = 10
    if packet.polarity in {"ironic", "fluid"}:
        ips += 10
        iv += 10
    if packet.decay_pattern == "flip":
        ips += 10
        iv += 10
    if packet.taboo_level == "medium":
        ips += 5
        iv += 5
    if packet.taboo_level == "high":
        ips += 10
        iv += 10

    sdr = 20 if packet.velocity == "slow" else 35 if packet.velocity == "fast" else 55
    if packet.decay_pattern == "volatile":
        sdr += 10
    elif packet.decay_pattern == "flip":
        sdr += 5
    elif packet.decay_pattern == "revive":
        sdr -= 5
    elif packet.decay_pattern == "institutionalize":
        sdr -= 10

    cls = CLS_BY_DECAY[packet.decay_pattern]
    if packet.level in {"L1", "L6"}:
        cls += 5

    return {
        "STI": _clamp(sti),
        "CP": _clamp(cp),
        "IPS": _clamp(ips),
        "SDR": _clamp(sdr),
        "NMC": _clamp(nmc),
        "ARF": _clamp(arf),
        "SDI": _clamp(sdi),
        "IV": _clamp(iv),
        "CLS": _clamp(cls),
        "SSF": _clamp(ssf),
    }


def compute_seed_metrics_v1(packet: SlangPacketV1 | Mapping[str, Any]) -> SlangMetricsV1:
    """
    Deterministic metrics scorer for SlangPacket.v1.

    Uses only packet fields, no external data, no randomness.
    Seed overrides are respected to preserve the canonical α mapping.
    """
    try:
        pkt = packet if isinstance(packet, SlangPacketV1) else SlangPacketV1.model_validate(packet)
    except ValidationError as exc:
        fields = [".".join(map(str, err.get("loc", []))) for err in exc.errors()]
        reason = f"missing or invalid fields: {', '.join(sorted(set(fields)))}"
        return SlangMetricsV1.not_computable(reason=reason, method=SEED_METHOD)

    metrics = _base_metrics(pkt)
    if pkt.seed_overrides:
        for key, value in pkt.seed_overrides.items():
            metrics[key] = _clamp(int(value))

    return SlangMetricsV1(
        **metrics,
        status="ok",
        method=SEED_METHOD,
    )


def load_slang_hist_v1(path: Path | None = None) -> List[SlangPacketV1]:
    """
    Load SLANG-HIST.v1 packets with embedded metrics (read-only).
    """
    seed_path = path or _seed_path()
    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    seed = SlangHistSeedV1.model_validate(payload)
    return list(seed.packets)


def validate_seed_metrics_v1(
    packets: Iterable[SlangPacketV1] | None = None,
) -> List[Dict[str, Any]]:
    """
    Compare computed metrics against embedded metrics for the α seed set.
    Returns mismatches (empty list means all good).
    """
    pkts = list(packets) if packets is not None else load_slang_hist_v1()
    mismatches: List[Dict[str, Any]] = []
    for pkt in pkts:
        if pkt.metrics is None:
            mismatches.append({"packet_id": pkt.packet_id, "error": "missing metrics"})
            continue
        computed = compute_seed_metrics_v1(pkt)
        if computed.model_dump() != pkt.metrics.model_dump():
            mismatches.append(
                {
                    "packet_id": pkt.packet_id,
                    "expected": pkt.metrics.model_dump(),
                    "actual": computed.model_dump(),
                }
            )
    return mismatches


def stable_packet_json(packet: SlangPacketV1 | Mapping[str, Any]) -> str:
    """
    Stable serialization (sorted keys) for invariance checks.
    """
    pkt = packet if isinstance(packet, SlangPacketV1) else SlangPacketV1.model_validate(packet)
    return stable_json_dumps(pkt.model_dump(mode="json"))


def build_slang_observation_payload(
    packets: Iterable[SlangPacketV1] | None = None,
) -> Dict[str, Any]:
    """
    Observation-only payload for Oracle Signal Layer.
    This does not affect prediction weights (Dual-Lane principle).
    """
    pkts = list(packets) if packets is not None else load_slang_hist_v1()
    items = [
        {
            "packet_id": pkt.packet_id,
            "term": pkt.term,
            "metrics": (pkt.metrics or compute_seed_metrics_v1(pkt)).model_dump(),
        }
        for pkt in pkts
    ]
    return {
        "mode": "OBSERVATION_ONLY",
        "artifact": "SLANG-HIST.v1",
        "method": SEED_METHOD.model_dump(),
        "evidence": "none (no frequency series yet)",
        "items": items,
    }
