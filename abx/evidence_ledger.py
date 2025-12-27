from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return _sha256_bytes((text or "").encode("utf-8", errors="replace"))


def sha256_file(path: str) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


@dataclass(frozen=True)
class EvidenceEvent:
    ts: str
    run_id: str
    term: str
    kind: str
    source: str
    sha256: str
    observed_date: str = ""
    publisher: str = ""
    channel: str = ""
    claim: str = ""
    tags: List[str] | None = None
    weight: float = 0.5
    mav: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d.get("tags") is None:
            d["tags"] = []
        if d.get("mav") is None:
            d["mav"] = {}
        return d


class EvidenceLedger:
    """
    Append-only JSONL ledger. Deterministic: sha256 acts as dedupe key.
    """

    def __init__(self, ledger_path: str) -> None:
        self.ledger_path = ledger_path
        os.makedirs(os.path.dirname(ledger_path), exist_ok=True)

    def append(self, ev: EvidenceEvent) -> None:
        line = json.dumps(ev.to_dict(), ensure_ascii=False)
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def load_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.ledger_path):
            return []
        out: List[Dict[str, Any]] = []
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    if isinstance(d, dict):
                        out.append(d)
                except Exception:
                    continue
        return out


def make_url_event(
    *,
    run_id: str,
    term: str,
    url: str,
    channel: str,
    observed_date: str = "",
    publisher: str = "",
    tags: Optional[List[str]] = None,
    weight: float = 0.5,
    claim: str = "",
    mav: Optional[Dict[str, Any]] = None,
) -> EvidenceEvent:
    return EvidenceEvent(
        ts=_utc_now_iso(),
        run_id=run_id,
        term=term,
        kind="url",
        source=url,
        sha256=sha256_text(url),
        observed_date=observed_date,
        publisher=publisher,
        channel=channel,
        claim=claim,
        tags=tags or [],
        weight=float(weight),
        mav=mav or {},
    )


def make_note_event(
    *,
    run_id: str,
    term: str,
    note: str,
    channel: str,
    tags: Optional[List[str]] = None,
    weight: float = 0.35,
    claim: str = "",
    mav: Optional[Dict[str, Any]] = None,
) -> EvidenceEvent:
    return EvidenceEvent(
        ts=_utc_now_iso(),
        run_id=run_id,
        term=term,
        kind="note",
        source=note[:2800],
        sha256=sha256_text(note),
        channel=channel,
        claim=claim,
        tags=tags or [],
        weight=float(weight),
        mav=mav or {},
    )
