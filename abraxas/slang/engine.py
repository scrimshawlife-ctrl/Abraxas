"""Slang Emergence Engine (SEE) - main engine for slang detection and analysis."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from abraxas.core.registry import OperatorRegistry
from abraxas.core.resonance_frame import ResonanceFrame
from abraxas.slang.models import SlangCluster, SlangToken, OperatorReadout
from abraxas.slang.operators.base import Operator, OperatorStatus
from abraxas.slang.operators.builtin_ctd import CTDOperator


class SlangEngine:
    """
    Slang Emergence Engine (SEE).

    Detects emergent slang patterns from resonance frames and applies operators
    to classify and analyze them.
    """

    def __init__(
        self,
        registry_path: str | None = None,
        enable_oasis: bool = True,
        builtin_operators: bool = True,
    ):
        """
        Initialize SEE.

        Args:
            registry_path: Path to operator registry
            enable_oasis: Enable OAS integration
            builtin_operators: Load built-in operators (like CTD)
        """
        self.registry = OperatorRegistry(registry_path)
        self.enable_oasis = enable_oasis
        self.operators: list[Operator] = []

        # Load operators
        if builtin_operators:
            self._load_builtin_operators()
        self._load_registry_operators()

    def _load_builtin_operators(self) -> None:
        """Load built-in operators."""
        ctd = CTDOperator()
        self.operators.append(ctd)

    def _load_registry_operators(self) -> None:
        """Load operators from registry."""
        # Load canonical operators from registry
        entries = self.registry.list_canonical()

        for entry in entries:
            # In a full implementation, this would dynamically instantiate operators
            # For now, we'll skip dynamic loading but the architecture is in place
            pass

    def reload_operators(self) -> None:
        """Reload operators from registry (called after OAS updates)."""
        self.operators.clear()
        self._load_builtin_operators()
        self._load_registry_operators()

    def tokenize(self, text: str) -> list[SlangToken]:
        """Simple tokenization (deterministic)."""
        # Simple whitespace tokenization for now
        tokens = text.split()
        return [
            SlangToken(token=t, position=i, features={})
            for i, t in enumerate(tokens)
        ]

    def detect_clusters(self, frames: list[ResonanceFrame]) -> list[SlangCluster]:
        """
        Detect slang clusters from frames.

        This is a simplified implementation. In production, this would use
        more sophisticated clustering (phonetic similarity, temporal windowing, etc.)
        """
        clusters: dict[str, SlangCluster] = {}

        # Group by simple pattern matching (deterministic)
        for frame in frames:
            tokens = self.tokenize(frame.text)

            # Create cluster ID from frame text hash (deterministic)
            cluster_id = hashlib.md5(frame.text.encode()).hexdigest()[:16]

            if cluster_id not in clusters:
                clusters[cluster_id] = SlangCluster(
                    cluster_id=cluster_id,
                    tokens=tokens,
                    features={},
                    window=(frame.ts, frame.ts),
                    evidence_refs=[frame.event_id],
                )
            else:
                # Update existing cluster
                cluster = clusters[cluster_id]
                cluster.tokens.extend(tokens)
                cluster.evidence_refs.append(frame.event_id)
                # Update window
                if cluster.window:
                    start, end = cluster.window
                    cluster.window = (min(start, frame.ts), max(end, frame.ts))

        return list(clusters.values())

    def apply_operators(
        self, clusters: list[SlangCluster], frames: list[ResonanceFrame]
    ) -> list[SlangCluster]:
        """
        Apply all active operators to clusters.

        Returns clusters with operator readouts attached.
        """
        # Create frame lookup for operator context
        frame_map = {f.event_id: f for f in frames}

        for cluster in clusters:
            # Reconstruct text from cluster
            text = " ".join([t.token for t in cluster.tokens])

            # Get first frame for context
            frame = None
            if cluster.evidence_refs:
                frame = frame_map.get(cluster.evidence_refs[0])

            # Apply each operator
            for operator in self.operators:
                readout = operator.apply(text, frame)
                if readout:
                    cluster.add_readout(readout)

        return clusters

    def process_frames(self, frames: list[ResonanceFrame]) -> list[SlangCluster]:
        """
        Full processing pipeline: frames -> clusters -> operator application.

        Returns annotated clusters.
        """
        clusters = self.detect_clusters(frames)
        clusters = self.apply_operators(clusters, frames)
        return clusters

    def trigger_oasis_cycle(
        self, frames: list[ResonanceFrame], clusters: list[SlangCluster]
    ) -> None:
        """
        Trigger OAS discovery cycle (called periodically or on demand).

        This integrates with the OAS pipeline to discover new operators.
        """
        if not self.enable_oasis:
            return

        # Import here to avoid circular dependency
        from abraxas.oasis.collector import OASCollector
        from abraxas.oasis.miner import OASMiner
        from abraxas.oasis.proposer import OASProposer
        from abraxas.oasis.validator import OASValidator
        from abraxas.oasis.stabilizer import OASStabilizer
        from abraxas.oasis.canonizer import OASCanonizer

        # Run OAS pipeline
        collector = OASCollector()
        miner = OASMiner()
        proposer = OASProposer()
        validator = OASValidator()
        stabilizer = OASStabilizer()
        canonizer = OASCanonizer(self.registry)

        # Pipeline execution
        # Note: This is a simplified version; full implementation would be more complex
        patterns = miner.mine(clusters, frames)
        candidates = proposer.propose(patterns, clusters, frames)

        for candidate in candidates:
            report = validator.validate(candidate, frames, self.operators)
            if report.passed:
                stab_state = stabilizer.check_stability(candidate, [report])
                if stab_state.stable:
                    decision = canonizer.canonize(candidate, report, stab_state)
                    if decision.adopted:
                        # Reload operators to include new one
                        self.reload_operators()
