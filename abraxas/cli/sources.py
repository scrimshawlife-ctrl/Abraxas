"""CLI helpers for SourceAtlas."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from abraxas.sources.atlas import list_sources
from abraxas.sources.runtime import run_source_once, run_sources_batch
from abraxas.sources.types import SourceWindow


def list_sources_cmd() -> int:
    sources = [spec.canonical_payload() for spec in list_sources()]
    print(json.dumps(sources, indent=2, sort_keys=True))
    return 0


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_json_object(payload: str, *, field_name: str) -> Dict[str, Any]:
    try:
        value = json.loads(payload)
    except Exception as exc:  # pragma: no cover - error path tested via callers
        raise SystemExit(f"Invalid --{field_name} payload: {exc}")
    if not isinstance(value, dict):
        raise SystemExit(f"Invalid --{field_name} payload: must decode to a JSON object")
    return value


def _emit_envelope(envelope: Dict[str, Any], *, out: str | None = None) -> None:
    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(envelope, indent=2, sort_keys=True))


def fetch_source_cmd(
    source_id: str,
    *,
    start_utc: str | None = None,
    end_utc: str | None = None,
    params_json: str = "{}",
    cache_dir: str | None = None,
    run_id: str = "sources_fetch",
) -> int:
    params = _parse_json_object(params_json, field_name="params-json")

    window = SourceWindow(start_utc=start_utc, end_utc=end_utc)
    packets = run_source_once(
        source_id=source_id,
        window=window,
        params=params,
        cache_dir=Path(cache_dir) if cache_dir else None,
        run_ctx={"run_id": run_id},
    )
    print(json.dumps([packet.model_dump() for packet in packets], indent=2, sort_keys=True))
    return 0


def fetch_sources_batch_cmd(
    source_ids: List[str],
    *,
    start_utc: str | None = None,
    end_utc: str | None = None,
    default_params_json: str = "{}",
    params_by_source_json: str = "{}",
    cache_dir: str | None = None,
    run_id: str = "sources_fetch_batch",
    strict: bool = False,
) -> int:
    default_params = _parse_json_object(default_params_json, field_name="default-params-json")
    params_by_source = _parse_json_object(params_by_source_json, field_name="params-by-source-json")

    window = SourceWindow(start_utc=start_utc, end_utc=end_utc)
    report = run_sources_batch(
        source_ids=source_ids,
        window=window,
        params_by_source=params_by_source,
        default_params=default_params,
        cache_dir=Path(cache_dir) if cache_dir else None,
        run_ctx={"run_id": run_id},
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if (report.get("ok") or not strict) else 2


def refresh_sources_cmd(
    source_ids: List[str],
    *,
    refresh_all: bool = False,
    start_utc: str | None = None,
    end_utc: str | None = None,
    default_params_json: str = "{}",
    params_by_source_json: str = "{}",
    cache_dir: str | None = None,
    run_id: str = "sources_refresh",
    out: str | None = None,
    strict: bool = False,
) -> int:
    selected_ids = list(source_ids or [])
    if refresh_all:
        selected_ids = [spec.source_id for spec in list_sources()]
    if not selected_ids:
        raise SystemExit("No sources selected. Provide --source-id or --all.")

    default_params = _parse_json_object(default_params_json, field_name="default-params-json")
    params_by_source = _parse_json_object(params_by_source_json, field_name="params-by-source-json")

    window = SourceWindow(start_utc=start_utc, end_utc=end_utc)
    report = run_sources_batch(
        source_ids=selected_ids,
        window=window,
        params_by_source=params_by_source,
        default_params=default_params,
        cache_dir=Path(cache_dir) if cache_dir else None,
        run_ctx={"run_id": run_id},
    )
    envelope = {
        "kind": "source_refresh_report.v0",
        "generated_at_utc": _utc_now_iso(),
        "run_id": run_id,
        "report": report,
    }

    _emit_envelope(envelope, out=out)
    return 0 if (report.get("ok") or not strict) else 2
