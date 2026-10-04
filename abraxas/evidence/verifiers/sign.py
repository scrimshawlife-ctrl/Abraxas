"""
Sign Relation Verifier — production implementation for Semion evidence verification.

Verifies structural consistency of Peircean sign relations.
Checks: sign class validity, interpretant coherence, representamen-object alignment,
Peircean category consistency, thirdness recursion.
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/Users/appliedalchemylabs/Abraxas")

import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from functools import lru_cache
from abraxas.evidence.contract import EvidenceEnvelope


# ─── PEIRCEAN TAXONOMY ────────────────────────────────────────────────

PEIRCE_CLASSES = {
    # Existence (Firstness)
    "qualisign": {"category": "firstness", "type": "quality", "definition": "sign as mere quality/possibility"},
    "sinsign": {"category": "firstness", "type": "individual", "definition": "sign as individual event/fact"},
    "legisign": {"category": "firstness", "type": "law", "definition": "sign as general type/law/habit"},

    # Relation (Secondness)
    "icon": {"category": "secondness", "type": "similarity", "definition": "sign resembles object by quality"},
    "index": {"category": "secondness", "type": "contiguity", "definition": "sign physically connected to object"},
    "symbol": {"category": "secondness", "type": "convention", "definition": "sign by rule/habit/interpretant"},

    # Interpretant (Thirdness)
    "rheme": {"category": "thirdness", "type": "possibility", "definition": "sign as mere possibility/suggestion"},
    "dicent": {"category": "thirdness", "type": "actuality", "definition": "sign as actual fact/proposition"},
    "argument": {"category": "thirdness", "type": "necessity", "definition": "sign as argument/law/governance"},
}

# Valid Peircean combinations (existence-thirdness-relation)
VALID_COMBINATIONS = {
    ("qualisign", "rheme", "icon"), ("qualisign", "rheme", "index"), ("qualisign", "rheme", "symbol"),
    ("qualisign", "dicent", "icon"), ("qualisign", "dicent", "index"), ("qualisign", "dicent", "symbol"),
    ("qualisign", "argument", "icon"), ("qualisign", "argument", "index"), ("qualisign", "argument", "symbol"),
    ("sinsign", "rheme", "icon"), ("sinsign", "rheme", "index"), ("sinsign", "rheme", "symbol"),
    ("sinsign", "dicent", "icon"), ("sinsign", "dicent", "index"), ("sinsign", "dicent", "symbol"),
    ("sinsign", "argument", "icon"), ("sinsign", "argument", "index"), ("sinsign", "argument", "symbol"),
    ("legisign", "rheme", "icon"), ("legisign", "rheme", "index"), ("legisign", "rheme", "symbol"),
    ("legisign", "dicent", "icon"), ("legisign", "dicent", "index"), ("legisign", "dicent", "symbol"),
    ("legisign", "argument", "icon"), ("legisign", "argument", "index"), ("legisign", "argument", "symbol"),
}

EXISTENCE_CATEGORIES = {"qualisign", "sinsign", "legisign"}
THIRDNESS_CATEGORIES = {"rheme", "dicent", "argument"}
RELATION_CATEGORIES = {"icon", "index", "symbol"}

CATEGORY_ORDER = {
    "firstness": ["qualisign", "sinsign", "legisign"],
    "secondness": ["icon", "index", "symbol"],
    "thirdness": ["rheme", "dicent", "argument"],
}


@lru_cache(maxsize=128)
def parse_sign_class(sign_class: str) -> Optional[Tuple[str, str, str]]:
    """Parse sign_class string into (existence, thirdness, relation)."""
    parts = sign_class.split("-")
    return tuple(parts) if len(parts) == 3 else None


@lru_cache(maxsize=128)
def validate_sign_class(sign_class: str) -> Tuple[bool, List[str]]:
    """Validate a sign class against Peircean taxonomy."""
    errors = []
    parsed = parse_sign_class(sign_class)

    if not parsed:
        errors.append(f"Invalid sign class format (need existence-thirdness-relation): {sign_class}")
        return False, errors

    existence, thirdness, relation = parsed

    if existence not in EXISTENCE_CATEGORIES:
        errors.append(f"Invalid existence category: {existence} (must be: qualisign, sinsign, legisign)")
    if thirdness not in THIRDNESS_CATEGORIES:
        errors.append(f"Invalid thirdness category: {thirdness} (must be: rheme, dicent, argument)")
    if relation not in RELATION_CATEGORIES:
        errors.append(f"Invalid relation category: {relation} (must be: icon, index, symbol)")

    if parsed not in VALID_COMBINATIONS:
        errors.append(f"Invalid Peircean combination: {sign_class}")

    return len(errors) == 0, errors


def check_interpretant_coherence(relation_steps: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    """Check if interpretants are coherent with relations."""
    if not relation_steps:
        return 1.0, []
    
    errors = []
    coherent_count = 0
    
    for step in relation_steps:
        relation = step.get("relation", "")
        result = step.get("result", "")
        
        # Optimized: Use early exit and pre-compiled patterns would be better
        # For now, keep the logic but make it more efficient
        if relation in ["causes", "implies", "triggers", "entails"]:
            if any(neg in result.lower() for neg in ["not", "false", "negate", "contradict"]):
                errors.append(f"Contradictory: {relation} but result negates: {result}")
            else:
                coherent_count += 1
        elif relation in ["means", "signifies", "represents", "indicates"]:
            if "not" in result.lower() and "not means" not in result.lower():
                errors.append(f"Contradictory: {relation} but result negates: {result}")
            else:
                coherent_count += 1
        else:
            coherent_count += 1  # Neutral relation
    
    total = len(relation_steps)
    return (coherent_count / total) if total > 0 else 1.0, errors


def check_representamen_object_alignment(relation_steps: List[Dict[str, Any]]) -> float:
    """Check if representamen and object are properly aligned in relation chain."""
    if len(relation_steps) < 2:
        return 1.0

    aligned = 0
    for i in range(len(relation_steps) - 1):
        curr_obj = relation_steps[i].get("object", "")
        next_subj = relation_steps[i + 1].get("subject", "")

        if curr_obj and next_subj and curr_obj == next_subj:
            aligned += 1

    return aligned / (len(relation_steps) - 1)


def check_category_consistency(relation_steps: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    """Check if sign classes maintain consistent Peircean categories across chain."""
    if not relation_steps:
        return 1.0, []

    errors = []
    consistent = 0
    total_checked = 0

    for step in relation_steps:
        sign_class = step.get("sign_class", "")
        if not sign_class:
            continue

        total_checked += 1
        valid, errs = validate_sign_class(sign_class)
        if valid:
            consistent += 1
        else:
            errors.extend(errs)

    return (consistent / total_checked) if total_checked > 0 else 1.0, errors


def check_thirdness_recursion(relation_steps: List[Dict[str, Any]]) -> float:
    """Check if thirdness (interpretant) category properly escalates through chain."""
    if len(relation_steps) < 2:
        return 1.0

    thirdness_values = []
    for step in relation_steps:
        sign_class = step.get("sign_class", "")
        parsed = parse_sign_class(sign_class)
        if parsed:
            thirdness = parsed[1]
            # rheme=0 (possibility), dicent=1 (actuality), argument=2 (necessity)
            mapping = {"rheme": 0, "dicent": 1, "argument": 2}
            thirdness_values.append(mapping.get(thirdness, 0))

    if len(thirdness_values) < 2:
        return 1.0

    # Thirdness should not decrease (escalating interpretant)
    violations = sum(1 for i in range(len(thirdness_values) - 1)
                     if thirdness_values[i] > thirdness_values[i + 1])

    return 1.0 - (violations / (len(thirdness_values) - 1))


# ─── SIGN RELATION VERIFIER ──────────────────────────────────────────

class SignRelationVerifier:
    """Verifies structural consistency of Semion sign relation evidence."""

    @property
    def evidence_type(self) -> str:
        return "SIGN_RELATION"

    @property
    def name(self) -> str:
        return "SignRelationVerifier"

    def __init__(
        self,
        min_interpretant_coherence: float = 0.7,
        min_representamen_alignment: float = 0.6,
        min_category_consistency: float = 0.7,
        min_thirdness_recursion: float = 0.5,
    ):
        self.min_interpretant_coherence = min_interpretant_coherence
        self.min_representamen_alignment = min_representamen_alignment
        self.min_category_consistency = min_category_consistency
        self.min_thirdness_recursion = min_thirdness_recursion

    def verify(self, envelope: EvidenceEnvelope) -> Dict[str, Any]:
        if envelope.engine != "semion":
            return {"passed": False, "escalate": True, "details": {"reason": "Engine is not semion"}}

        # Extract all relation steps from candidate outputs
        all_steps = []
        for candidate in envelope.candidate_outputs:
            for step in candidate.relation_steps:
                all_steps.append({
                    "relation": step.relation,
                    "subject": step.subject,
                    "object": step.object,
                    "result": step.result,
                    "sign_class": step.metadata.get("sign_class", ""),
                    "confidence": step.confidence,
                })

        contradictions = []

        # 1. Sign class validity
        class_valid = True
        class_errors = []
        for step in all_steps:
            sign_class = step.get("sign_class", "")
            if sign_class:
                valid, errs = validate_sign_class(sign_class)
                if not valid:
                    class_valid = False
                    class_errors.extend(errs)
                    contradictions.extend(errs)

        # 2. Interpretant coherence
        interpretant_coherence, interpretant_errors = check_interpretant_coherence(all_steps)
        contradictions.extend(interpretant_errors)

        # 3. Representamen-object alignment
        representamen_alignment = check_representamen_object_alignment(all_steps)

        # 4. Category consistency
        category_consistency, category_errors = check_category_consistency(all_steps)
        contradictions.extend(category_errors)

        # 5. Thirdness recursion
        thirdness_recursion = check_thirdness_recursion(all_steps)

        details = {
            "sign_class_valid": class_valid,
            "interpretant_coherence": interpretant_coherence,
            "representamen_object_alignment": representamen_alignment,
            "peircean_category_consistency": category_consistency,
            "thirdness_recursion": thirdness_recursion,
            "total_steps": len(all_steps),
            "contradictions": contradictions,
        }

        is_valid = (
            class_valid and
            interpretant_coherence >= self.min_interpretant_coherence and
            representamen_alignment >= self.min_representamen_alignment and
            category_consistency >= self.min_category_consistency and
            thirdness_recursion >= self.min_thirdness_recursion
        )

        escalate = not class_valid or len(contradictions) > 2

        return {
            "passed": is_valid,
            "escalate": escalate,
            "details": details
        }


# Test
if __name__ == "__main__":
    class MockCandidate:
        def __init__(self, steps):
            self.relation_steps = steps

    class MockEnvelope:
        engine = "semion"
        candidate_outputs = [
            MockCandidate([
                type('Step', (), {
                    'relation': 'causes',
                    'subject': 'A',
                    'object': 'B',
                    'result': 'B occurs',
                    'confidence': 0.9,
                    'metadata': {'sign_class': 'legisign-dicent-index'}
                })(),
                type('Step', (), {
                    'relation': 'triggers',
                    'subject': 'B',
                    'object': 'C',
                    'result': 'C occurs',
                    'confidence': 0.85,
                    'metadata': {'sign_class': 'sinsign-rheme-icon'}
                })(),
            ])
        ]

    verifier = SignRelationVerifier()
    result = verifier.verify(MockEnvelope())
    print(f"SignRelationVerifier test:")
    print(f"  Passed: {result['passed']}")
    print(f"  Details: {result['details']}")

    # Test validation
    test_classes = [
        "legisign-dicent-index",
        "sinsign-rheme-icon",
        "qualisign-dicent-symbol",
        "invalid-class",
        "qualisign-rheme-icon",
        "legisign-argument-symbol",
        "invalid-format",
    ]
    print("\nSign class validation:")
    for sc in test_classes:
        valid, errors = validate_sign_class(sc)
        print(f"  {sc}: {'VALID' if valid else 'INVALID'} {errors if not valid else ''}")