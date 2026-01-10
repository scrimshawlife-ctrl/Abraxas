"""Jetson-specific detection helpers (best-effort)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class JetsonStatus:
    platform: str
    gpu_present: bool
    clocks_pinned: bool
    power_mode: Optional[str]


def detect_jetson() -> JetsonStatus:
    platform = "unknown"
    gpu_present = False
    clocks_pinned = False
    power_mode = None

    model_path = Path("/proc/device-tree/model")
    if model_path.exists():
        model = model_path.read_text(encoding="utf-8").strip("\x00")
        platform = model.lower().replace(" ", "-")
        gpu_present = "nvidia" in platform or "jetson" in platform

    nvpmodel_path = Path("/etc/nvpmodel.conf")
    if nvpmodel_path.exists():
        power_mode = "nvpmodel"

    clocks_pinned = Path("/var/run/nvidia/jetson_clocks_active").exists()

    return JetsonStatus(
        platform=platform,
        gpu_present=gpu_present,
        clocks_pinned=clocks_pinned,
        power_mode=power_mode,
    )


def pin_clocks() -> bool:
    marker = Path("/var/run/nvidia/jetson_clocks_active")
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("pinned", encoding="utf-8")
        return True
    except Exception:
        return False
