from __future__ import annotations

import re
import unicodedata
from typing import List, Set

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z\-']+")


def ascii_fold(s: str) -> str:
    s2 = unicodedata.normalize("NFKD", s)
    s2 = "".join(ch for ch in s2 if not unicodedata.combining(ch))
    return s2


def normalize_text(s: str) -> str:
    s = ascii_fold(s)
    s = s.lower()
    return s


def extract_tokens(text: str) -> List[str]:
    """
    Deterministic token extraction:
    - letters + internal hyphens/apostrophes
    - emits raw tokens (lowercased later in normalize_token)
    """
    return _WORD_RE.findall(text)


def normalize_token(tok: str) -> str:
    t = normalize_text(tok)
    # remove leading/trailing punctuation remnants from regex capture
    t = t.strip("-'")
    # collapse internal repeats of hyphen/apostrophe sequences
    t = re.sub(r"[-']{2,}", "-", t)
    return t


def split_hyphenated(tok: str) -> List[str]:
    # keep the joined token AND split parts upstream if desired
    return [p for p in tok.split("-") if p]


def is_stopish(tok: str, stop: Set[str]) -> bool:
    return tok in stop


def filter_token(tok: str, min_len: int) -> bool:
    # accept only alphabetic tokens after stripping hyphens/apostrophes
    bare = tok.replace("-", "").replace("'", "")
    if len(bare) < min_len:
        return False
    if not bare.isalpha():
        return False
    return True
