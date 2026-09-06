"""Local JSON evidence sink for TimesFM Shadow packets."""

from __future__ import annotations

from pathlib import Path

from abraxas.core.canonical import canonical_json
from abraxas.sources.timesfm_shadow.constants import LATEST_PACKET_NAME
from abraxas.sources.timesfm_shadow.packets import TimesFMShadowForecastV0, assert_shadow_locks


def write_shadow_packet(packet: TimesFMShadowForecastV0, out_dir: Path) -> Path:
    assert_shadow_locks(packet)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(packet.model_dump()) + "\n"
    hashed = out_dir / f"timesfm_shadow_forecast.v0.{packet.packet_hash()[:16]}.json"
    latest = out_dir / LATEST_PACKET_NAME
    hashed.write_text(payload, encoding="utf-8")
    latest.write_text(payload, encoding="utf-8")
    return latest
