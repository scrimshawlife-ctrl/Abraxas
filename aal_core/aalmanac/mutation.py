from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Set
import json

DEFAULT_LEXICON_PATH = Path("out/config/baseline_lexicon.json")


def load_reference_dictionary(*, lexicon_path: Optional[Path] = None) -> Set[str]:
    path = lexicon_path or DEFAULT_LEXICON_PATH
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    if isinstance(data, dict):
        return {str(k).lower() for k in data.keys() if k}
    if isinstance(data, list):
        return {str(item).lower() for item in data if item}
    return set()


def detect_mutation(term_canonical: str, *, lexicon: Iterable[str]) -> str:
    term = term_canonical.lower()
    lex = {str(x).lower() for x in lexicon}
    if term and term not in lex:
        return "neologism"
    return "context_shift"
