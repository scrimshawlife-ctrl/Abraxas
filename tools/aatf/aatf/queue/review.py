from __future__ import annotations

from typing import Any, Dict
import json

from aatf.queue.states import PENDING
from aatf.storage import local_ledger_path


def enqueue_review(record: Dict[str, Any]) -> None:
    ledger = local_ledger_path("review_queue")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    payload = {"status": PENDING, "record": record}
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")
