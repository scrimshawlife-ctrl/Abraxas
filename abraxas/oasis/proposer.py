"""OAS Proposer: converts mined patterns to OperatorCandidate drafts."""

from __future__ import annotations

from datetime import datetime, timezone

from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_canonical_json
from abraxas.core.resonance_frame import ResonanceFrame
from abraxas.oasis.miner import MinedPattern
from abraxas.oasis.models import OperatorCandidate, OperatorStatus
from abraxas.slang.models import SlangCluster


class OASProposer:
    """
    Proposes OperatorCandidate objects from mined patterns.

    Converts raw patterns into structured operator candidates with provenance.
    """

    def __init__(self):
        pass

    def propose(
        self,
        patterns: list[MinedPattern],
        clusters: list[SlangCluster],
        frames: list[ResonanceFrame],
    ) -> list[OperatorCandidate]:
        """
        Generate operator candidates from mined patterns.

        Returns deterministic list of candidates.
        """
        candidates: list[OperatorCandidate] = []

        for pattern in patterns:
            candidate = self._pattern_to_candidate(pattern, clusters, frames)
            if candidate:
                candidates.append(candidate)

        # Sort for determinism
        candidates.sort(key=lambda c: c.operator_id)

        return candidates

    def _pattern_to_candidate(
        self,
        pattern: MinedPattern,
        clusters: list[SlangCluster],
        frames: list[ResonanceFrame],
    ) -> OperatorCandidate | None:
        """Convert a single pattern to an operator candidate."""
        pattern_type = pattern.get("pattern_type", "unknown")
        signature = pattern.get("signature", "")

        # Generate deterministic operator ID from pattern signature
        operator_id = f"oasis_{hash_canonical_json(pattern)[:16]}"

        # Build candidate based on pattern type
        if pattern_type == "cooccurrence":
            return self._cooccurrence_candidate(operator_id, pattern, clusters, frames)
        elif pattern_type == "drift":
            return self._drift_candidate(operator_id, pattern, clusters, frames)
        elif pattern_type == "phonetic":
            return self._phonetic_candidate(operator_id, pattern, clusters, frames)
        else:
            return None

    def _cooccurrence_candidate(
        self,
        operator_id: str,
        pattern: MinedPattern,
        clusters: list[SlangCluster],
        frames: list[ResonanceFrame],
    ) -> OperatorCandidate:
        """Create candidate for co-occurrence pattern."""
        tokens = pattern.get("tokens", [])
        frequency = pattern.get("frequency", 0)

        # Build provenance
        evidence_hashes = [hash_canonical_json(f.model_dump()) for f in frames[:10]]
        provenance = ProvenanceBundle(
            inputs=[
                ProvenanceRef(
                    scheme="pattern", path=pattern.get("signature", ""), sha256=hash_canonical_json(pattern)
                )
            ],
            transforms=["cooccurrence_analysis"],
            metrics={"frequency": float(frequency)},
            created_by="oasis_proposer",
        )

        # Discovery window
        start_ts = min(f.ts for f in frames) if frames else datetime.now(timezone.utc)
        end_ts = max(f.ts for f in frames) if frames else datetime.now(timezone.utc)

        discovery_window = {
            "start_ts": start_ts.isoformat(),
            "end_ts": end_ts.isoformat(),
            "sources": list(set(f.source for f in frames)),
        }

        candidate = OperatorCandidate(
            operator_id=operator_id,
            label=f"Cooccurrence: {' + '.join(tokens)}",
            class_tags=["cooccurrence", "emergent"],
            triggers=[f"\\b{t}\\b" for t in tokens],
            readouts=[f"cooc_{tokens[0]}_{tokens[1]}" if len(tokens) >= 2 else "cooccurrence"],
            failure_modes=["sparse_data", "overfitting"],
            scope={"pattern_type": "cooccurrence", "tokens": tokens},
            tests=[f"Should fire when both {tokens[0]} and {tokens[1]} appear"],
            provenance=provenance,
            discovery_window=discovery_window,
            evidence_hashes=evidence_hashes,
            candidate_score=min(1.0, frequency / 10.0),
            version="1.0.0",
            status=OperatorStatus.STAGING,
        )

        return candidate

    def _drift_candidate(
        self,
        operator_id: str,
        pattern: MinedPattern,
        clusters: list[SlangCluster],
        frames: list[ResonanceFrame],
    ) -> OperatorCandidate:
        """Create candidate for drift pattern."""
        token = pattern.get("token", "")
        frequency = pattern.get("frequency", 0)
        growth_rate = pattern.get("growth_rate", 0)

        evidence_hashes = [hash_canonical_json(f.model_dump()) for f in frames[:10]]
        provenance = ProvenanceBundle(
            inputs=[
                ProvenanceRef(
                    scheme="pattern", path=pattern.get("signature", ""), sha256=hash_canonical_json(pattern)
                )
            ],
            transforms=["drift_analysis"],
            metrics={"frequency": float(frequency), "growth_rate": float(growth_rate)},
            created_by="oasis_proposer",
        )

        start_ts = min(f.ts for f in frames) if frames else datetime.now(timezone.utc)
        end_ts = max(f.ts for f in frames) if frames else datetime.now(timezone.utc)

        discovery_window = {
            "start_ts": start_ts.isoformat(),
            "end_ts": end_ts.isoformat(),
            "sources": list(set(f.source for f in frames)),
        }

        candidate = OperatorCandidate(
            operator_id=operator_id,
            label=f"Drift: {token}",
            class_tags=["drift", "temporal"],
            triggers=[f"\\b{token}\\b"],
            readouts=["emerging", "trending"],
            failure_modes=["temporal_decay", "fad"],
            scope={"pattern_type": "drift", "token": token},
            tests=[f"Should detect increasing usage of {token}"],
            provenance=provenance,
            discovery_window=discovery_window,
            evidence_hashes=evidence_hashes,
            candidate_score=min(1.0, growth_rate / 3.0),
            version="1.0.0",
            status=OperatorStatus.STAGING,
        )

        return candidate

    def _phonetic_candidate(
        self,
        operator_id: str,
        pattern: MinedPattern,
        clusters: list[SlangCluster],
        frames: list[ResonanceFrame],
    ) -> OperatorCandidate:
        """Create candidate for phonetic pattern."""
        pattern_name = pattern.get("name", "")
        frequency = pattern.get("frequency", 0)

        evidence_hashes = [hash_canonical_json(f.model_dump()) for f in frames[:10]]
        provenance = ProvenanceBundle(
            inputs=[
                ProvenanceRef(
                    scheme="pattern", path=pattern.get("signature", ""), sha256=hash_canonical_json(pattern)
                )
            ],
            transforms=["phonetic_analysis"],
            metrics={"frequency": float(frequency)},
            created_by="oasis_proposer",
        )

        start_ts = min(f.ts for f in frames) if frames else datetime.now(timezone.utc)
        end_ts = max(f.ts for f in frames) if frames else datetime.now(timezone.utc)

        discovery_window = {
            "start_ts": start_ts.isoformat(),
            "end_ts": end_ts.isoformat(),
            "sources": list(set(f.source for f in frames)),
        }

        candidate = OperatorCandidate(
            operator_id=operator_id,
            label=f"Phonetic: {pattern_name}",
            class_tags=["phonetic", "orthographic"],
            triggers=[pattern_name],
            readouts=["phonetic_marker", pattern_name],
            failure_modes=["context_dependent", "ambiguous"],
            scope={"pattern_type": "phonetic", "name": pattern_name},
            tests=[f"Should detect {pattern_name} patterns"],
            provenance=provenance,
            discovery_window=discovery_window,
            evidence_hashes=evidence_hashes,
            candidate_score=min(1.0, frequency / 5.0),
            version="1.0.0",
            status=OperatorStatus.STAGING,
        )

        return candidate
