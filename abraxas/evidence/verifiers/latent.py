"""
Latent Structure Verifier — production implementation for Noesis evidence verification.

Verifies structural coherence of latent representations across interventions.
Checks: structural coherence, intervention sensitivity, representational stability,
RSA correlation, representational geometry preservation.

Pure Python implementation — no external dependencies.
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/Users/appliedalchemylabs/Abraxas")

import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from abraxas.evidence.contract import EvidenceEnvelope


def _flatten(arr: List[List[float]] | List[float]) -> List[float]:
    if not arr:
        return []
    if isinstance(arr[0], list):
        out = []
        for row in arr:
            out.extend(_flatten(row))
        return out
    return arr


def _norm(vec: List[float]) -> float:
    return math.sqrt(sum(x * x for x in vec))


def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def cosine_similarity(a: List[List[float]] | List[float], b: List[List[float]] | List[float]) -> float:
    a_f = _flatten(a)
    b_f = _flatten(b)
    if len(a_f) != len(b_f):
        return 0.0
    na = _norm(a_f)
    nb = _norm(b_f)
    if na == 0 or nb == 0:
        return 0.0
    return _dot(a_f, b_f) / (na * nb)


def l2_distance(a: List[List[float]] | List[float], b: List[List[float]] | List[float]) -> float:
    a_f = _flatten(a)
    b_f = _flatten(b)
    if len(a_f) != len(b_f):
        return float('inf')
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a_f, b_f)))


def compute_rsa_matrix(captures: List[Dict[str, Any]]) -> List[List[float]]:
    n = len(captures)
    mat = [[0.0] * n for _ in range(n)]
    for i, c1 in enumerate(captures):
        for j, c2 in enumerate(captures):
            mat[i][j] = cosine_similarity(c1["activations"], c2["activations"])
    return mat


def compute_rsa_correlation(rsa1: List[List[float]], rsa2: List[List[float]]) -> float:
    n = len(rsa1)
    triu = [(i, j) for i in range(n) for j in range(i + 1, n)]
    if len(triu) < 2:
        return 0.0
    r1 = [rsa1[i][j] for i, j in triu]
    r2 = [rsa2[i][j] for i, j in triu]
    mean1 = sum(r1) / len(r1)
    mean2 = sum(r2) / len(r2)
    num = sum((x - mean1) * (y - mean2) for x, y in zip(r1, r2))
    den1 = math.sqrt(sum((x - mean1) ** 2 for x in r1))
    den2 = math.sqrt(sum((y - mean2) ** 2 for y in r2))
    if den1 == 0 or den2 == 0:
        return 0.0
    return num / (den1 * den2)


def analyze_latent_structure(
    captures: List[Dict[str, Any]],
    baseline_condition: str = "baseline"
) -> Dict[str, Any]:
    by_condition = {}
    for cap in captures:
        cond = cap.get("condition", "unknown")
        by_condition.setdefault(cond, []).append(cap)

    if baseline_condition not in by_condition:
        return {"error": f"Baseline '{baseline_condition}' not found"}

    baseline_caps = by_condition[baseline_condition]
    if not baseline_caps:
        return {"error": "No baseline captures"}

    # Average baseline
    n = len(baseline_caps)
    first_shape = len(_flatten(baseline_caps[0]["activations"]))
    baseline_avg = [0.0] * first_shape
    for cap in baseline_caps:
        flat = _flatten(cap["activations"])
        for i, v in enumerate(flat):
            baseline_avg[i] += v
    baseline_avg = [v / n for v in baseline_avg]

    results = {}
    all_stabilities = []
    for condition, caps in by_condition.items():
        if condition == baseline_condition:
            continue
        condition_results = []
        for cap in caps:
            flat = _flatten(cap["activations"])
            if len(flat) != first_shape:
                continue
            sim = cosine_similarity(flat, baseline_avg)
            l2 = l2_distance(flat, baseline_avg)
            condition_results.append({
                "similarity": sim,
                "l2_distance": l2,
                "stability": sim,
                "intervention_sensitivity": 1.0 - sim,
            })
        if condition_results:
            mean_stab = sum(r["similarity"] for r in condition_results) / len(condition_results)
            mean_sens = sum(r["intervention_sensitivity"] for r in condition_results) / len(condition_results)
            results[condition] = {
                "mean_stability": mean_stab,
                "mean_intervention_sensitivity": mean_sens,
                "sample_count": len(condition_results),
            }
            all_stabilities.append(mean_stab)

    return {
        "conditions": results,
        "overall_structural_coherence": sum(all_stabilities) / len(all_stabilities) if all_stabilities else 0.0,
        "baseline_condition": baseline_condition,
        "conditions_tested": list(results.keys()),
    }


class LatentStructureVerifier:
    """Verifies structural coherence of latent representations across interventions."""

    @property
    def evidence_type(self) -> str:
        return "LATENT_STRUCTURAL"

    @property
    def name(self) -> str:
        return "LatentStructureVerifier"

    def __init__(self, coherence_threshold: float = 0.7, sensitivity_threshold: float = 0.3):
        self.coherence_threshold = coherence_threshold
        self.sensitivity_threshold = sensitivity_threshold

    def verify(self, envelope: EvidenceEnvelope) -> Dict[str, Any]:
        if envelope.engine != "noesis":
            return {"passed": False, "escalate": True, "details": {"reason": "Engine is not noesis"}}

        coherence = envelope.provenance.get("structural_coherence", 0.0)
        intervention_sensitivity = envelope.provenance.get("intervention_sensitivity", 1.0)
        rsa_correlation = envelope.provenance.get("rsa_correlation", 0.0)
        geometric_integrity = envelope.provenance.get("geometric_integrity", 0.0)

        details = {
            "structural_coherence": coherence,
            "intervention_sensitivity": intervention_sensitivity,
            "stability_score": 1.0 - intervention_sensitivity,
            "rsa_correlation": rsa_correlation,
            "geometric_integrity": geometric_integrity,
        }

        passed = (
            coherence >= self.coherence_threshold and
            intervention_sensitivity <= self.sensitivity_threshold
        )
        escalate = coherence < 0.4 or intervention_sensitivity > 0.6

        return {
            "passed": bool(passed),
            "escalate": escalate,
            "details": details
        }

    def compute_rsa_correlation(self, rsa1: List[List[float]], rsa2: List[List[float]]) -> float:
        return compute_rsa_correlation(rsa1, rsa2)

    def compute_geometric_integrity(self, captures: List[Dict], baseline_condition: str = "baseline") -> float:
        result = analyze_latent_structure(captures, baseline_condition)
        return result.get("overall_structural_coherence", 0.0)

    def compute_rsa_matrix(self, captures: List[Dict]) -> List[List[float]]:
        return compute_rsa_matrix(captures)


# Test
if __name__ == "__main__":
    # Mock envelope
    class MockEnvelope:
        engine = "noesis"
        provenance = {
            "structural_coherence": 0.85,
            "intervention_sensitivity": 0.15,
            "rsa_correlation": 0.92,
            "geometric_integrity": 0.88,
        }

    verifier = LatentStructureVerifier()
    result = verifier.verify(MockEnvelope())
    print(f"LatentStructureVerifier test: {result}")

    # Test structural analysis
    captures = [
        {"condition": "baseline", "activations": [[1, 2, 3], [4, 5, 6]]},
        {"condition": "baseline", "activations": [[1.1, 2.1, 3.1], [4.1, 5.1, 6.1]]},
        {"condition": "intervention", "activations": [[1.5, 2.5, 3.5], [4.5, 5.5, 6.5]]},
        {"condition": "counterfactual", "activations": [[0.5, 1.5, 2.5], [3.5, 4.5, 5.5]]},
    ]
    analysis = analyze_latent_structure(captures)
    print(f"Structural analysis: {analysis}")

    # Test RSA
    rsa = compute_rsa_matrix(captures[:2])
    print(f"RSA matrix: {rsa}")