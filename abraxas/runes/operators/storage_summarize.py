"""ABX-STORAGE_SUMMARIZE rune operator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from abraxas.storage.index import StorageIndex
from abraxas.storage.lifecycle_ir import load_lifecycle_ir
from abraxas.storage.lifecycle_run import summarize_storage


def apply_storage_summarize(
    *,
    index_path: str,
    now_utc: str,
    strict_execution: bool = True,
) -> Dict[str, Any]:
    index = StorageIndex.from_jsonl(Path(index_path))
    lifecycle_ir = load_lifecycle_ir(now_utc)
    summary = summarize_storage(index, now_utc, lifecycle_ir)
    return {"summary": summary, "ir_hash": lifecycle_ir.ir_hash()}
