from __future__ import annotations

import re
from typing import List

_CAMEL_RE = re.compile(r"([a-z])([A-Z])")


def tokenize(term_raw: str) -> List[str]:
    """
    Deterministic tokenizer.
    This function alone decides SINGLE vs COMPOUND eligibility.
    """
    t = (term_raw or "").strip()
    if not t:
        return []

    t = t.replace("’", "'")
    t = t.replace("-", " - ")
    t = t.replace("_", " _ ")
    t = _CAMEL_RE.sub(r"\1 \2", t)

    tokens = t.split()
    tokens = [tok for tok in tokens if tok not in {"-", "_"}]
    tokens = [tok.lower() for tok in tokens]
    return tokens
