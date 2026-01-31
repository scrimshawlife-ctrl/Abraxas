from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from aal_core.aalmanac.tokenizer import tokenize


@dataclass(frozen=True)
class TermClassification:
    term_class: str
    tokens: List[str]
    note: Optional[str] = None


def canonicalize(tokens: List[str]) -> str:
    return " ".join(tokens)


def classify_term(tokens: List[str]) -> str:
    if len(tokens) == 1:
        return "single"
    if len(tokens) == 2:
        return "compound"
    return "phrase"


def classify_term_from_raw(term_raw: str, *, declared_class: Optional[str] = None) -> TermClassification:
    tokens = tokenize(term_raw)
    derived = classify_term(tokens)
    note = None
    term_class = derived
    if declared_class and declared_class != derived:
        note = "declared_class_mismatch"
    if declared_class == "single" and len(tokens) > 1:
        note = "forced_compound_from_multitoken"
        term_class = "compound"
    return TermClassification(term_class=term_class, tokens=tokens, note=note)
