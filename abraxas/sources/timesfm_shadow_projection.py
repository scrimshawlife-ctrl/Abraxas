"""Project a TimesFM Shadow packet to local Notion-shaped JSON.

This slice is SHADOW-only. It does not call Notion, mint Canon, or change
Forecast authority. `valid_for_forecast` is always false. The same packet
bytes and relative path yield the same projection JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Mapping, Sequence

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as SchemaValidationError

from abraxas.core.canonical import sha256_hex

SCHEMA_VERSION = "timesfm_shadow_notion_projection.v0"
PROJECTION_SOURCE_ID = "EXT.TIMESFM.2_5.v1"
PROJECTION_SEMANTICS = "generative_prior"
LANE = "SHADOW"
INFLUENCE = "NONE"
AUTHORITY_BADGE = "SHADOW_PROJECTION"
SCHEMA_NAME = "timesfm_shadow_notion_projection.v0.json"
_BLOCKED = (ValueError, OSError, SchemaValidationError, TypeError)


def projection_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / SCHEMA_NAME


def load_projection_schema() -> Mapping[str, object]:
    path = projection_schema_path()
    if not path.is_file():
        raise ValueError(f"projection schema not found: {path}")
    return _as_mapping(json.loads(path.read_text(encoding="utf-8")), "projection schema")


def validate_projection(projection: Mapping[str, object]) -> None:
    Draft202012Validator(load_projection_schema()).validate(projection)


def project_packet_path(packet_path: Path, *, repo_root: Path | None = None) -> dict[str, object]:
    raw = _read_packet_bytes(packet_path)
    return project_packet_bytes(raw, local_path=_relative_path(packet_path, repo_root))


def project_packet_bytes(raw: bytes, local_path: str) -> dict[str, object]:
    packet = _parse_packet(raw)
    projection = _build_projection(packet, packet_hash=sha256_hex(raw), local_path=local_path)
    validate_projection(projection)
    return projection


def write_projection(projection: Mapping[str, object], out_path: Path) -> Path:
    validate_projection(projection)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dict(projection), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    out_path.write_text(payload, encoding="utf-8")
    return out_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m abraxas.sources.timesfm_shadow_projection",
        description=(
            "Project TimesFMShadowForecast.v0 to timesfm_shadow_notion_projection.v0. "
            "Local JSON only. Does not write Notion or Forecast."
        ),
    )
    parser.add_argument("--packet", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        projection = project_packet_path(Path(args.packet))
        write_projection(projection, Path(args.out))
    except _BLOCKED as exc:
        sys.stderr.write(f"timesfm_shadow_projection: blocked: {exc}\n")
        return 2
    sys.stdout.write(f"timesfm_shadow_projection: wrote {projection['packet_hash']}\n")
    return 0


def _read_packet_bytes(packet_path: Path) -> bytes:
    if not packet_path.is_file():
        raise ValueError(f"packet file not found: {packet_path}")
    return packet_path.read_bytes()


def _parse_packet(raw: bytes) -> Mapping[str, object]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("packet is not valid JSON") from exc
    return _as_mapping(payload, "packet")


def _build_projection(
    packet: Mapping[str, object],
    *,
    packet_hash: str,
    local_path: str,
) -> dict[str, object]:
    history = _as_mapping(packet.get("history"), "history")
    forecast = _as_mapping(packet.get("forecast"), "forecast")
    horizon = _as_int(forecast.get("horizon"), "forecast.horizon")
    if horizon < 1:
        raise ValueError("forecast.horizon must be >= 1")
    history_len = _as_int(history.get("window_n"), "history.window_n")
    if history_len < 1:
        raise ValueError("history.window_n must be >= 1")
    projection: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "packet_hash": packet_hash,
        "source_id": PROJECTION_SOURCE_ID,
        "series_ref": _as_str(packet.get("source_id"), "source_id"),
        "hf_model": _as_str(packet.get("model_id"), "model_id"),
        "lane": LANE,
        "influence": INFLUENCE,
        "valid_for_forecast": False,
        "semantics": PROJECTION_SEMANTICS,
        "history_len": history_len,
        "horizon": horizon,
        "quantiles": _quantiles(forecast, horizon),
        "fold_in_feeds": _fold_in_feeds(packet),
        "authority_badge": AUTHORITY_BADGE,
        "local_path": _as_str(local_path, "local_path"),
    }
    _put_optional(projection, "hf_revision", _optional_str(packet, "hf_revision"))
    _put_optional(projection, "license", _optional_str(packet, "license"))
    _put_optional(projection, "seed", _optional_int(packet, "seed"))
    _put_optional(projection, "bzn", _optional_str(packet, "bzn"))
    _put_optional(projection, "mean_summary", _mean_summary(forecast))
    return projection


def _quantiles(forecast: Mapping[str, object], horizon: int) -> dict[str, list[float]]:
    block = _as_mapping(forecast.get("quantiles"), "forecast.quantiles")
    out: dict[str, list[float]] = {}
    for key in ("q10", "q50", "q90"):
        series = _as_float_list(block.get(key), f"forecast.quantiles.{key}")
        if len(series) != horizon:
            raise ValueError(f"forecast.quantiles.{key} length must equal horizon")
        out[key] = series
    return out


def _mean_summary(forecast: Mapping[str, object]) -> dict[str, float | int] | None:
    if "mean" not in forecast:
        return None
    series = _as_float_list(forecast["mean"], "forecast.mean")
    return {"last": series[-1], "n": len(series)}


def _fold_in_feeds(packet: Mapping[str, object]) -> list[dict[str, str]]:
    if "fold_in" not in packet:
        return []
    block = _as_mapping(packet["fold_in"], "fold_in")
    feeds = block.get("feeds", [])
    if not isinstance(feeds, list):
        raise ValueError("fold_in.feeds must be a list")
    return [_fold_in_feed(feed, index) for index, feed in enumerate(feeds)]


def _fold_in_feed(feed: object, index: int) -> dict[str, str]:
    row = _as_mapping(feed, f"fold_in.feeds[{index}]")
    target = _as_str(row.get("target"), f"fold_in.feeds[{index}].target")
    return {"target": target, "authority": "none"}


def _optional_str(packet: Mapping[str, object], key: str) -> str | None:
    if key not in packet:
        return None
    return _as_str(packet[key], key)


def _optional_int(packet: Mapping[str, object], key: str) -> int | None:
    if key not in packet:
        return None
    return _as_int(packet[key], key)


def _put_optional(dest: dict[str, object], key: str, value: object | None) -> None:
    if value is not None:
        dest[key] = value


def _relative_path(packet_path: Path, repo_root: Path | None) -> str:
    root = (repo_root or Path.cwd()).resolve()
    resolved = packet_path.expanduser().resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return Path(packet_path).as_posix()


def _as_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _as_str(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _as_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _as_float_list(value: object, label: str) -> list[float]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    out: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{label} must contain numbers")
        out.append(float(item))
    return out


if __name__ == "__main__":
    raise SystemExit(main())
