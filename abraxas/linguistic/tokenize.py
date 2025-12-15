# abraxas/linguistic/tokenize.py
# Tokenization utilities

from __future__ import annotations
import re
from typing import List

_WORD_RE = re.compile(r"[A-Za-z0-9']+")

def tokens(text: str) -> List[str]:
    """Extract alphanumeric tokens from text."""
    return [t.lower() for t in _WORD_RE.findall(text)]

def ngrams(chars: str, n: int) -> List[str]:
    """Generate character n-grams."""
    if n <= 0:
        return []
    s = chars
    if len(s) < n:
        return [s] if s else []
    return [s[i:i+n] for i in range(len(s)-n+1)]
