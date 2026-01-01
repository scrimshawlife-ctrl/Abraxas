from __future__ import annotations
import json
import sys
import time
from typing import Any, Dict, Optional

def log(event: str, **fields: Any) -> None:
    # journald-friendly JSON line logs (stable keys order at output stage)
    obj: Dict[str, Any] = {"ts": int(time.time()), "event": event}
    for k in sorted(fields.keys()):
        obj[k] = fields[k]
    sys.stdout.write(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
    sys.stdout.flush()

def warn(event: str, **fields: Any) -> None:
    log(event, level="WARN", **fields)

def err(event: str, **fields: Any) -> None:
    log(event, level="ERROR", **fields)
