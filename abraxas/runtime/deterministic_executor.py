"""Deterministic parallel executor with serial commit ordering."""

from __future__ import annotations

import concurrent.futures
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Tuple

from abraxas.runtime.concurrency import ConcurrencyConfig
from abraxas.runtime.work_units import WorkUnit


@dataclass(frozen=True)
class WorkResult:
    unit_id: str
    key: Tuple[Any, ...]
    output_refs: Dict[str, Any]
    bytes_processed: int
    stage: str


@dataclass(frozen=True)
class ParallelExecutionResult:
    results: List[WorkResult]
    max_inflight_bytes: int
    workers_used: int
    wall_ms: int


def execute_parallel(
    work_units: Iterable[WorkUnit],
    *,
    config: ConcurrencyConfig,
    stage: str,
    handler: Callable[[WorkUnit], WorkResult],
) -> ParallelExecutionResult:
    units = list(work_units)
    if not units:
        return ParallelExecutionResult(results=[], max_inflight_bytes=0, workers_used=0, wall_ms=0)

    workers = config.workers_for_stage(stage)
    if not config.enabled:
        workers = 1

    inflight_limit = max(0, int(config.max_inflight_bytes))
    limiter = _ByteLimiter(inflight_limit) if inflight_limit else None
    inflight_lock = threading.Lock()
    inflight_bytes = 0
    max_inflight = 0

    def wrapped_handler(unit: WorkUnit) -> WorkResult:
        nonlocal inflight_bytes, max_inflight
        if limiter:
            limiter.acquire(unit.input_bytes)
        with inflight_lock:
            inflight_bytes += unit.input_bytes
            max_inflight = max(max_inflight, inflight_bytes)
        try:
            return handler(unit)
        finally:
            with inflight_lock:
                inflight_bytes -= unit.input_bytes
            if limiter:
                limiter.release(unit.input_bytes)

    start = time.monotonic()
    results: List[WorkResult] = []

    if workers <= 1:
        for unit in units:
            results.append(wrapped_handler(unit))
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(wrapped_handler, unit) for unit in units]
            for future in futures:
                results.append(future.result())

    wall_ms = int((time.monotonic() - start) * 1000)
    return ParallelExecutionResult(
        results=results,
        max_inflight_bytes=max_inflight if inflight_limit else max_inflight,
        workers_used=workers,
        wall_ms=wall_ms,
    )


def commit_results(results: Iterable[WorkResult]) -> List[WorkResult]:
    return sorted(results, key=lambda result: result.key)


class _ByteLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = max(0, limit)
        self._available = self.limit
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def acquire(self, amount: int) -> None:
        amt = min(self.limit, max(0, int(amount)))
        if amt == 0:
            return
        with self._cond:
            while self._available < amt:
                self._cond.wait()
            self._available -= amt

    def release(self, amount: int) -> None:
        amt = min(self.limit, max(0, int(amount)))
        if amt == 0:
            return
        with self._cond:
            self._available = min(self.limit, self._available + amt)
            self._cond.notify_all()
