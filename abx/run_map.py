from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date
from typing import List


TS_RE = re.compile(r"(20\\d{2})[-_]?(\\d{2})[-_]?(\\d{2})")


@dataclass(frozen=True)
class RunMap:
    run_id: str
    oracle_paths: List[str]


def resolve_oracle_paths_for_day(oracle_paths: List[str], day: date) -> List[str]:
    ymd = day.strftime("%Y-%m-%d")
    ymd_compact = day.strftime("%Y%m%d")

    matched: List[str] = []
    for path in oracle_paths:
        filename = os.path.basename(path)
        if ymd in filename or ymd_compact in filename:
            matched.append(path)
            continue
        match = TS_RE.search(filename)
        if not match:
            continue
        yy, mm, dd = match.group(1), match.group(2), match.group(3)
        if f"{yy}-{mm}-{dd}" == ymd:
            matched.append(path)

    return sorted(matched) if matched else sorted(oracle_paths)


def build_run_map(day: date, oracle_paths: List[str], prefix: str = "DAILY") -> RunMap:
    run_id = f"{day.isoformat()}_{prefix}"
    return RunMap(run_id=run_id, oracle_paths=resolve_oracle_paths_for_day(oracle_paths, day))
