from __future__ import annotations

from typing import List, Set, Tuple


# v0.1: heuristic domain mapping by pointer prefixes (keep narrow; expand later with governance).
DOMAIN_POINTER_PREFIXES: List[Tuple[str, str]] = [
    ("symbolic", "/symbolic_compression"),
    ("signal", "/signal_layer"),
    ("slang", "/slang"),
    ("aalmanac", "/aalmanac"),
    ("overlay", "/interpretive_overlay"),
    # Oracle v2-shaped artifacts (used by fixtures in this repo)
    ("oracle", "/compression"),
]


def domain_for_pointer(pointer: str) -> str:
    for domain, prefix in DOMAIN_POINTER_PREFIXES:
        if pointer == prefix or pointer.startswith(prefix.rstrip("/") + "/"):
            return domain
    return "unknown"


def domains_for_evidence_pointers(pointers: Set[str]) -> Set[str]:
    return {domain_for_pointer(p) for p in pointers} or {"unknown"}

