from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CanonicalResult:
    text: str
    meta: dict[str, str | int]


def canonicalize(text: str, source_path: Path, content_type: str) -> CanonicalResult:
    normalized = unicodedata.normalize("NFC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\x00", "")
    lines = []
    for line in normalized.split("\n"):
        cleaned = re.sub(r"\s+", " ", line).rstrip()
        lines.append(cleaned)
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    collapsed = "\n".join(lines)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    meta = {
        "content_type": content_type,
        "source_path": str(source_path),
        "byte_count": len(text.encode("utf-8")),
    }
    return CanonicalResult(text=collapsed, meta=meta)
