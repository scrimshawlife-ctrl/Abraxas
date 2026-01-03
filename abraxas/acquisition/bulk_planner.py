"""Bulk pull planner that turns manifests into finite steps."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from abraxas.acquisition.manifest_schema import ManifestArtifact
from abraxas.acquisition.plan_schema import BulkPullPlan, PlanStep
from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.policy.utp import PortfolioTuningIR


DATE_PATTERNS = [
    re.compile(r"(\d{4})-(\d{2})-(\d{2})"),
    re.compile(r"(\d{4})(\d{2})(\d{2})"),
]


@dataclass(frozen=True)
class BulkPlanResult:
    plan: BulkPullPlan
    overflow_urls: List[str]


def build_bulk_plan(
    *,
    source_id: str,
    window_utc: Dict[str, Optional[str]],
    manifest: ManifestArtifact,
    budgets: PortfolioTuningIR,
    created_at_utc: str,
) -> BulkPlanResult:
    urls = list(manifest.urls)
    selected, overflow = _filter_by_window(urls, window_utc)

    max_requests = budgets.ubv.max_requests_per_run
    if len(selected) > max_requests:
        overflow = overflow + selected[max_requests:]
        selected = selected[:max_requests]

    steps: List[PlanStep] = []
    for idx, url in enumerate(selected):
        step_id = sha256_hex(canonical_json({"url": url, "idx": idx, "source_id": source_id}))[:16]
        steps.append(
            PlanStep(
                step_id=step_id,
                action="DOWNLOAD",
                url_or_key=url,
                expected_bytes=None,
                cache_policy="REQUIRED",
                codec_hint=None,
                notes=None,
                deterministic_order_index=idx,
            )
        )

    plan = BulkPullPlan.build(
        source_id=source_id,
        created_at_utc=created_at_utc,
        window_utc=window_utc,
        manifest_id=manifest.manifest_id,
        steps=steps,
    )

    return BulkPlanResult(plan=plan, overflow_urls=overflow)


def _filter_by_window(urls: List[str], window_utc: Dict[str, Optional[str]]) -> Tuple[List[str], List[str]]:
    window_start = _parse_date(window_utc.get("start"))
    window_end = _parse_date(window_utc.get("end"))

    dated = []
    undated = []
    for url in urls:
        date = _extract_date(url)
        if date:
            dated.append((url, date))
        else:
            undated.append(url)

    if window_start or window_end:
        filtered = [url for url, date in dated if _date_in_window(date, window_start, window_end)]
        filtered.sort()
        undated_sorted = sorted(undated)
        return filtered + undated_sorted, []

    if dated:
        dated_sorted = sorted(dated, key=lambda item: item[0], reverse=True)
        return [url for url, _ in dated_sorted], []

    return sorted(undated), []


def _extract_date(url: str) -> Optional[datetime]:
    for pattern in DATE_PATTERNS:
        match = pattern.search(url)
        if not match:
            continue
        try:
            year, month, day = [int(part) for part in match.groups()]
            return datetime(year, month, day)
        except ValueError:
            continue
    return None


def _date_in_window(date: datetime, start: Optional[datetime], end: Optional[datetime]) -> bool:
    if start and date < start:
        return False
    if end and date > end:
        return False
    return True


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None
