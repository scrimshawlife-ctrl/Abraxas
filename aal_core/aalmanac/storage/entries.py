from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import time

from aal_core.aalmanac.filter import quality_gate, rejection_reason
from aal_core.aalmanac.storage.rejections import append_rejection

DEFAULT_AALMANAC_DIR = Path.home() / ".aal" / "aalmanac"
DEFAULT_ENTRIES_PATH = DEFAULT_AALMANAC_DIR / "entries.jsonl"
DEFAULT_REVIEW_QUEUE_PATH = DEFAULT_AALMANAC_DIR / "review_queue.jsonl"


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")


def append_entry(entry: Dict[str, Any], *, entries_path: Optional[Path] = None) -> None:
    target = entries_path or DEFAULT_ENTRIES_PATH
    _ensure_dir(target)
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def load_entries(*, entries_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    target = entries_path or DEFAULT_ENTRIES_PATH
    if not target.exists():
        return []
    entries: List[Dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def append_review_queue(entry: Dict[str, Any], *, queue_path: Optional[Path] = None) -> None:
    target = queue_path or DEFAULT_REVIEW_QUEUE_PATH
    _ensure_dir(target)
    payload = dict(entry)
    payload.setdefault("queued_at_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")


def should_queue_for_review(entry: Dict[str, Any]) -> bool:
    signals = entry.get("signals", {})
    drift = entry.get("drift", {})
    plausibility = float(signals.get("plausibility", 0.0) or 0.0)
    drift_charge = float(drift.get("drift_charge", 0.0) or 0.0)
    mutation_type = str(entry.get("mutation_type", ""))
    return plausibility < 0.45 or drift_charge > 0.85 or mutation_type == "phonetic_flip"


def ingest_entries(
    entries: Iterable[Dict[str, Any]],
    *,
    entries_path: Optional[Path] = None,
    queue_path: Optional[Path] = None,
) -> None:
    for entry in entries:
        if not quality_gate(entry):
            append_rejection(entry, reason=rejection_reason(entry))
            continue
        append_entry(entry, entries_path=entries_path)
        if should_queue_for_review(entry):
            append_review_queue(entry, queue_path=queue_path)
