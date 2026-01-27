from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

from .text_subword import TextSubwordCartridge
from .types import SymbolicDomainCartridge
from ..lexicon import Lexicon


def load_registry(
    *,
    lexicon: Lexicon,
    canary_subwords: Optional[Iterable[str]] = None,
) -> List[SymbolicDomainCartridge]:
    canary_list: Sequence[str] = sorted(set(canary_subwords or []))
    cartridges: List[SymbolicDomainCartridge] = [
        TextSubwordCartridge(lexicon=lexicon, canary_subwords=canary_list),
    ]
    return cartridges
