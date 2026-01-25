from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, List

from .provenance import sha256_hex


@dataclass(frozen=True)
class RuntimeLexicon:
    core_subwords: FrozenSet[str]
    canary_subwords: FrozenSet[str]
    runtime_hash: str


def _read_words(path: Path) -> List[str]:
    if not path.exists():
        return []
    out: List[str] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip().lower()
        if not s or s.startswith("#"):
            continue
        if s.isalpha():
            out.append(s)
    return sorted(set(out))


def load_canary_words(lanes_dir: Path) -> FrozenSet[str]:
    return frozenset(_read_words(lanes_dir / "canary.txt"))


def build_runtime_lexicon(core_subwords: FrozenSet[str], canary_subwords: FrozenSet[str]) -> RuntimeLexicon:
    payload = ("\n".join(sorted(core_subwords)) + "\n||\n" + "\n".join(sorted(canary_subwords)) + "\n").encode("utf-8")
    return RuntimeLexicon(core_subwords=core_subwords, canary_subwords=canary_subwords, runtime_hash=sha256_hex(payload))
