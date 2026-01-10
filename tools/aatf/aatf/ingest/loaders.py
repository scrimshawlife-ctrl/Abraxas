from __future__ import annotations

import json
import importlib
import importlib.util
from pathlib import Path
from typing import Tuple


def load_text(path: Path) -> Tuple[str, str]:
    return load_text_for_kind(path, kind="auto")


def load_text_for_kind(path: Path, kind: str) -> Tuple[str, str]:
    suffix = path.suffix.lower()
    if kind != "auto":
        suffix = f".{kind}"
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8"), suffix.lstrip(".")
    if suffix == ".json":
        raw = path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        return json.dumps(parsed, sort_keys=True, ensure_ascii=False), "json"
    if suffix == ".pdf":
        if importlib.util.find_spec("pypdf") is None:
            raise RuntimeError("pypdf not installed")
        pypdf = importlib.import_module("pypdf")
        reader = pypdf.PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text, "pdf"
    raise RuntimeError(f"Unsupported file type: {suffix}")
