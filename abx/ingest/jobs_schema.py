from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

Kind = Literal["url"]

@dataclass(frozen=True)
class IngestJob:
    name: str
    kind: Kind
    url: str
    every_s: int
    enabled: bool = True
    target: str = "universal"
    headless: str = "html"
    locale: str = "en-us"
    device_type: str = "desktop"

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "IngestJob":
        return IngestJob(
            name=str(d["name"]),
            kind=str(d.get("kind", "url")),  # type: ignore
            url=str(d["url"]),
            every_s=int(d.get("every_s", 3600)),
            enabled=bool(d.get("enabled", True)),
            target=str(d.get("target", "universal")),
            headless=str(d.get("headless", "html")),
            locale=str(d.get("locale", "en-us")),
            device_type=str(d.get("device_type", "desktop")),
        )

def load_jobs(path: str) -> List[IngestJob]:
    import json
    from pathlib import Path
    p = Path(path)
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    jobs = d.get("jobs", d) if isinstance(d, dict) else d
    out: List[IngestJob] = []
    for j in jobs:
        if isinstance(j, dict):
            out.append(IngestJob.from_dict(j))
    out.sort(key=lambda x: x.name)  # deterministic scheduling order
    return out
