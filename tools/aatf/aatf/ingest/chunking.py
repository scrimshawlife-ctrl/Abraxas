from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..provenance import sha256_hex


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    start: int
    end: int
    text: str


def chunk_text(text: str, size: int = 2000, overlap: int = 200) -> List[Chunk]:
    chunks: List[Chunk] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunk_text = text[start:end]
        chunk_id = sha256_hex(f"{text}:{start}:{end}")
        chunks.append(Chunk(chunk_id=chunk_id, start=start, end=end, text=chunk_text))
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks
