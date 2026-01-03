"""Deterministic measurement utilities for profiling."""

from __future__ import annotations

import os
import resource
import time
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class TimerResult:
    cpu_ms: int
    latency_ms: int


def monotonic_timer(start: float, end: float) -> int:
    return int((end - start) * 1000)


def process_cpu_ms() -> int:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return int((usage.ru_utime + usage.ru_stime) * 1000)


def process_rss_bytes() -> int | None:
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
    except Exception:
        return None
    rss_kb = getattr(usage, "ru_maxrss", None)
    if rss_kb is None:
        return None
    if os.uname().sysname.lower().startswith("darwin"):
        return int(rss_kb)
    return int(rss_kb) * 1024


def measure_duration(fn) -> Tuple[TimerResult, object]:
    cpu_before = process_cpu_ms()
    start = time.monotonic()
    output = fn()
    end = time.monotonic()
    cpu_after = process_cpu_ms()
    return TimerResult(cpu_ms=cpu_after - cpu_before, latency_ms=monotonic_timer(start, end)), output
