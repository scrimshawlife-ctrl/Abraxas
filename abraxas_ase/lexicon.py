from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

try:
    from .lexicon_generated import STOPWORDS, SUBWORDS
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "Missing generated lexicon artifacts. Run:\n"
        "  python -m abraxas_ase.tools.lexicon_update --in lexicon_sources --out abraxas_ase\n"
    ) from e


@dataclass(frozen=True)
class Lexicon:
    stopwords: FrozenSet[str]
    subwords: FrozenSet[str]


def build_default_lexicon() -> Lexicon:
    return Lexicon(stopwords=STOPWORDS, subwords=SUBWORDS)
