"""
Lexical Consistency Verifier — production implementation for Hyperlex evidence verification.

Verifies lineage consistency, virality coherence, semantic variation coherence,
neologism plausibility, and hyperstition stage alignment.
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/Users/appliedalchemylabs/Abraxas")

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from abraxas.evidence.contract import EvidenceEnvelope


@dataclass
class LineageAnalysis:
    family_id: str
    confidence: float
    branch_operator: str
    ancestral_terms: List[str] = field(default_factory=list)
    drift_score: float = 0.0


@dataclass
class ViralityAnalysis:
    hybrid_score: float
    velocity: float
    acceleration: float
    platform_concentration: float
    peak_velocity: float = 0.0


@dataclass
class SemanticVariation:
    sense: str
    driver: str
    polysemy_count: int
    contextual_stability: float


@dataclass
class Neologism:
    term: str
    formation: str
    confidence: float
    attestation_count: int


@dataclass
class HyperstitionStage:
    loop_stage: str
    confidence: float
    citation_graph_depth: int
    recursive_citations: int


class LexicalConsistencyVerifier:
    @property
    def evidence_type(self) -> str:
        return "LEXICAL_SEMANTIC"

    @property
    def name(self) -> str:
        return "LexicalConsistencyVerifier"

    # Lineage families from Hyperlex calibration
    LINEAGE_FAMILIES = {
        "betting-sharp": {"branch_operator": "sense_extension", "ancestral": ["sharp", "wise guy", "smart money"]},
        "crypto-degen": {"branch_operator": "cross_family_borrowing", "ancestral": ["degen", "ape", "diamond hands"]},
        "ai-native": {"branch_operator": "platform_compression", "ancestral": ["prompt engineering", "latent space", "embedding"]},
        "brainrot-aura": {"branch_operator": "irony_inversion", "ancestral": ["skibidi", "rizz", "gyatt"]},
        "kinship-address": {"branch_operator": "sense_extension", "ancestral": ["fam", "bro", "cuz"]},
        "political-status": {"branch_operator": "irony_inversion", "ancestral": ["based", "cringe", "woke"]},
        "gaming-meta": {"branch_operator": "platform_compression", "ancestral": ["meta", "nerf", "buff"]},
        "workplace-corp": {"branch_operator": "sense_extension", "ancestral": ["circle back", "sync", "bandwidth"]},
    }

    VIRALITY_COHERENCE_THRESHOLD = 0.3
    LINEAGE_CONSISTENCY_THRESHOLD = 0.42
    SEMANTIC_VARIATION_COHERENCE_THRESHOLD = 0.3
    NEOLOGISM_PLAUSIBILITY_THRESHOLD = 0.3
    HYPERSTITION_ALIGNMENT_THRESHOLD = 0.3

    def verify(self, envelope: EvidenceEnvelope) -> Dict[str, Any]:
        if envelope.engine != "hyperlex":
            return {"passed": False, "escalate": True, "details": {"reason": "Engine is not hyperlex"}}

        analysis = envelope.provenance.get("hyperlex_analysis", {})
        if not analysis:
            return {"passed": False, "escalate": True, "details": {"reason": "No Hyperlex analysis in provenance"}}

        contradictions = []

        # 1. Lineage consistency
        lineage_consistency = self._check_lineage_consistency(analysis, contradictions)

        # 2. Virality coherence
        virality_coherence = self._check_virality_coherence(analysis, contradictions)

        # 3. Semantic variation coherence
        semantic_variation_coherence = self._check_semantic_variation_coherence(analysis, contradictions)

        # 4. Neologism plausibility
        neologism_plausibility = self._check_neologism_plausibility(analysis, contradictions)

        # 5. Hyperstition stage alignment
        hyperstition_alignment = self._check_hyperstition_alignment(analysis, contradictions)

        is_consistent = (
            lineage_consistency >= self.LINEAGE_CONSISTENCY_THRESHOLD and
            virality_coherence >= self.VIRALITY_COHERENCE_THRESHOLD and
            semantic_variation_coherence >= self.SEMANTIC_VARIATION_COHERENCE_THRESHOLD and
            neologism_plausibility >= self.NEOLOGISM_PLAUSIBILITY_THRESHOLD and
            hyperstition_alignment >= self.HYPERSTITION_ALIGNMENT_THRESHOLD
        )

        return {
            "passed": is_consistent,
            "escalate": False,
            "details": {
                "lineage_consistency": lineage_consistency,
                "virality_coherence": virality_coherence,
                "semantic_variation_coherence": semantic_variation_coherence,
                "neologism_plausibility": neologism_plausibility,
                "hyperstition_stage_alignment": hyperstition_alignment,
                "contradictions": contradictions,
            }
        }

    def _check_lineage_consistency(self, analysis: Dict, contradictions: List[str]) -> float:
        lineage = analysis.get("lineage", {})
        family_id = lineage.get("family_id")
        confidence = lineage.get("confidence", 0.0)

        if family_id not in self.LINEAGE_FAMILIES:
            contradictions.append(f"Unknown lineage family: {family_id}")
            return 0.0

        family = self.LINEAGE_FAMILIES[family_id]
        drift = lineage.get("drift_score", 0.0)

        # Consistency = confidence * (1 - drift) * branch_operator_alignment
        branch_alignment = 1.0 if lineage.get("branch_operator") == family["branch_operator"] else 0.5

        return confidence * (1.0 - min(drift, 1.0)) * branch_alignment

    def _check_virality_coherence(self, analysis: Dict, contradictions: List[str]) -> float:
        virality = analysis.get("virality", {})
        hybrid = virality.get("hybrid_score", 0.0)
        velocity = virality.get("velocity", 0.0)
        acceleration = virality.get("acceleration", 0.0)

        if hybrid < 0.3 and velocity > 0.8:
            contradictions.append("High velocity with low hybrid score — possible inorganic spread")
        if acceleration > 2.0 and hybrid < 0.2:
            contradictions.append("Extreme acceleration with no hybrid signal — likely bot/coordinated")

        coherence = hybrid * min(1.0, velocity + 0.2) * (1.0 / (1.0 + max(0, acceleration - 1.0)))
        return coherence

    def _check_semantic_variation_coherence(self, analysis: Dict, contradictions: List[str]) -> float:
        sem_var = analysis.get("semantic_variation", {})
        sense = sem_var.get("sense", "")
        driver = sem_var.get("driver", "")
        polysemy = sem_var.get("polysemy_count", 1)
        stability = sem_var.get("contextual_stability", 0.5)

        if polysemy > 5 and stability < 0.3:
            contradictions.append(f"High polysemy ({polysemy}) with low stability ({stability})")

        coherence = stability * (1.0 / (1.0 + max(0, polysemy - 3) * 0.15))
        return coherence

    def _check_neologism_plausibility(self, analysis: Dict, contradictions: List[str]) -> float:
        neologisms = analysis.get("neologisms", [])
        if not neologisms:
            return 1.0  # No neologisms to check

        total = 0.0
        for neo in neologisms:
            term = neo.get("term", "")
            formation = neo.get("formation", "")
            confidence = neo.get("confidence", 0.0)
            attestation = neo.get("attestation_count", 0)

            # Check morphological plausibility
            morph_score = self._morphological_plausibility(term, formation)
            attest_score = min(1.0, attestation / 100.0)  # Cap at 100 attestations

            plaus = confidence * morph_score * attest_score
            total += plaus

            if plaus < 0.2:
                contradictions.append(f"Implausible neologism: {term} (formation: {formation})")

        return total / len(neologisms)

    def _morphological_plausibility(self, term: str, formation: str) -> float:
        """Score morphological plausibility based on formation type."""
        scores = {
            "compound_phrase": 0.9,
            "clipping": 0.85,
            "blending": 0.8,
            "acronym": 0.75,
            "derivation": 0.8,
            "borrowing": 0.7,
            "back_formation": 0.6,
            "conversion": 0.75,
            "onomatopoeia": 0.5,
        }
        return scores.get(formation, 0.4)

    def _check_hyperstition_alignment(self, analysis: Dict, contradictions: List[str]) -> float:
        hyper = analysis.get("hyperstition", {})
        stage = hyper.get("loop_stage", "DORMANT")
        confidence = hyper.get("confidence", 0.0)
        depth = hyper.get("citation_graph_depth", 0)
        recursive = hyper.get("recursive_citations", 0)

        stage_scores = {
            "DORMANT": 0.3,
            "EMERGING": 0.6,
            "ACTUALIZING": 0.8,
            "CANONICAL": 1.0,
            "DECAY": 0.2,
        }

        base = stage_scores.get(stage, 0.3)
        depth_bonus = min(0.2, depth * 0.02)
        recursive_penalty = min(0.3, recursive * 0.05)

        alignment = confidence * base + depth_bonus - recursive_penalty

        if stage == "CANONICAL" and depth < 3:
            contradictions.append("CANONICAL stage with insufficient citation depth")
            alignment *= 0.7

        return max(0.0, min(1.0, alignment))


# Test
if __name__ == "__main__":
    class MockEnvelope:
        engine = "hyperlex"
        provenance = {
            "hyperlex_analysis": {
                "lineage": {"family_id": "betting-sharp", "confidence": 0.85, "branch_operator": "sense_extension", "drift_score": 0.15},
                "virality": {"hybrid_score": 0.75, "velocity": 0.6, "acceleration": 0.5},
                "semantic_variation": {"sense": "tactical/quant", "driver": "tactical_edge", "polysemy_count": 2, "contextual_stability": 0.8},
                "neologisms": [{"term": "sharp money", "formation": "compound_phrase", "confidence": 0.8, "attestation_count": 50}],
                "hyperstition": {"loop_stage": "ACTUALIZING", "confidence": 0.85, "citation_graph_depth": 5, "recursive_citations": 2},
            }
        }

    verifier = LexicalConsistencyVerifier()
    result = verifier.verify(MockEnvelope())
    print(f"LexicalConsistencyVerifier test:")
    print(f"  Passed: {result['passed']}")
    print(f"  Details: {result['details']}")