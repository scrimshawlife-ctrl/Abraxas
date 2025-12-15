# abraxas/linguistic/phonetics.py
# Phonetic encoding utilities

from __future__ import annotations
import re

_ALPHA_RE = re.compile(r"[^a-z]+")

def _clean_alpha(s: str) -> str:
    """Remove non-alphabetic characters."""
    s = s.lower()
    s = _ALPHA_RE.sub("", s)
    return s

def soundex(word: str) -> str:
    """
    Deterministic Soundex (English-ish). Good enough as a stable phonetic proxy.
    """
    w = _clean_alpha(word)
    if not w:
        return ""
    first = w[0].upper()

    mapping = {
        **{c: "1" for c in "bfpv"},
        **{c: "2" for c in "cgjkqsxz"},
        **{c: "3" for c in "dt"},
        "l": "4",
        **{c: "5" for c in "mn"},
        "r": "6",
    }

    def code(c: str) -> str:
        return mapping.get(c, "0")

    out = [first]
    prev = code(w[0])
    for c in w[1:]:
        cd = code(c)
        if cd == "0":
            prev = cd
            continue
        if cd != prev:
            out.append(cd)
        prev = cd

    # Pad/trim to 4
    sx = "".join(out)[:4].ljust(4, "0")
    return sx

def phonetic_key(phrase: str) -> str:
    """
    Create a stable phonetic fingerprint for a multi-word token/phrase.
    """
    parts = [p for p in phrase.strip().split() if p]
    keys = [soundex(p) for p in parts]
    return "-".join([k for k in keys if k])
