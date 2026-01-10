# abraxas/operators/symbolic_compression.py
# ABRAXAS CORE MODULE
# Symbolic Compression Operator (SCO)
# Tier-1: Eggcorn Compression Operator (ECO)

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Literal, Optional
import math
import hashlib
import json

from abraxas.linguistic.transparency import TransparencyLexicon
from abraxas.linguistic.similarity import phonetic_similarity, intent_preservation_score
from abraxas.linguistic.rdv import rdv_from_context

CompressionStatus = Literal["proto", "emergent", "stabilizing"]
CompressionTier = Literal["ECO_T1", "SCO_T2"]

@dataclass(frozen=True)
class SymbolicCompressionEvent:
    event_type: str  # "SymbolicCompressionEvent"
    tier: CompressionTier
    original_token: str
    replacement_token: str
    domain: str

    phonetic_similarity: float
    semantic_transparency_delta: float
    intent_preservation_score: float

    compression_pressure: float         # CP
    symbolic_transparency_index: float  # STI(original)
    symbolic_load_capacity: float       # SLC
    replacement_direction_vector: Dict[str, float]  # RDV

    observed_frequency: int
    status: CompressionStatus
    transparency_lexicon_prov: str = ""
    provenance_sha256: str = ""  # Deterministic record hash

class SymbolicCompressionOperator:
    """
    SCO/ECO operator. Deterministic scoring & thresholds.
    """
    PHONETIC_THRESHOLD = 0.75
    INTENT_THRESHOLD = 0.70
    TRANSPARENCY_DELTA_THRESHOLD = 0.02

    def __init__(self, transparency: TransparencyLexicon):
        self.transparency = transparency

    def analyze(
        self,
        original_token: str,
        replacement_token: str,
        context_before: str,
        context_after: str,
        domain: str,
        observed_frequency: int
    ) -> Optional[SymbolicCompressionEvent]:
        ps = phonetic_similarity(original_token, replacement_token)
        ips = intent_preservation_score(context_before, context_after)

        sti0 = self.transparency.sti(original_token)
        sti1 = self.transparency.sti(replacement_token)
        dt = round(sti1 - sti0, 6)

        if dt <= 0:
            return None

        if not self._passes_thresholds(ps, dt, ips):
            return None

        cp = self._compression_pressure(ps, ips, observed_frequency)
        status = self._classify_status(cp)
        slc = round(1.0 - sti0, 6)

        # RDV from "after" context (where the replacement appears)
        rdv = rdv_from_context(context_after)

        tier: CompressionTier = "ECO_T1" if ps >= 0.85 and dt >= 0.18 else "SCO_T2"

        event = SymbolicCompressionEvent(
            event_type="SymbolicCompressionEvent",
            tier=tier,
            original_token=original_token,
            replacement_token=replacement_token,
            domain=domain,
            phonetic_similarity=round(ps, 6),
            semantic_transparency_delta=dt,
            intent_preservation_score=round(ips, 6),
            compression_pressure=cp,
            symbolic_transparency_index=round(sti0, 6),
            symbolic_load_capacity=slc,
            replacement_direction_vector=rdv,
            observed_frequency=int(observed_frequency),
            status=status,
            transparency_lexicon_prov=self.transparency.provenance_sha256,
            provenance_sha256=""  # filled below
        )
        return self._with_provenance(event)

    def _passes_thresholds(self, ps: float, dt: float, ips: float) -> bool:
        return (
            ps >= self.PHONETIC_THRESHOLD and
            dt >= self.TRANSPARENCY_DELTA_THRESHOLD and
            ips >= self.INTENT_THRESHOLD
        )

    def _compression_pressure(self, ps: float, ips: float, freq: int) -> float:
        # CP = (0.4*ps + 0.6*ips) * log1p(freq)
        f = math.log1p(max(0, int(freq)))
        return round((ps * 0.4 + ips * 0.6) * f, 6)

    def _classify_status(self, cp: float) -> CompressionStatus:
        if cp < 0.8:
            return "proto"
        if cp < 1.6:
            return "emergent"
        return "stabilizing"

    def _with_provenance(self, e: SymbolicCompressionEvent) -> SymbolicCompressionEvent:
        payload = {
            "event_type": e.event_type,
            "tier": e.tier,
            "original_token": e.original_token,
            "replacement_token": e.replacement_token,
            "domain": e.domain,
            "phonetic_similarity": e.phonetic_similarity,
            "semantic_transparency_delta": e.semantic_transparency_delta,
            "intent_preservation_score": e.intent_preservation_score,
            "compression_pressure": e.compression_pressure,
            "symbolic_transparency_index": e.symbolic_transparency_index,
            "symbolic_load_capacity": e.symbolic_load_capacity,
            "replacement_direction_vector": e.replacement_direction_vector,
            "observed_frequency": e.observed_frequency,
            "status": e.status,
            "transparency_lexicon_prov": e.transparency_lexicon_prov,
        }
        s = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        prov = hashlib.sha256(s).hexdigest()
        return SymbolicCompressionEvent(**{**payload, "provenance_sha256": prov})
