"""Deterministic device fingerprinting."""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.canonical import canonical_json, sha256_hex


def get_device_fingerprint(run_ctx: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cpu_arch = platform.machine().lower() or "unknown"
    platform_id = _platform_id()
    mem_total_bytes = _mem_total_bytes()
    storage_class = _storage_class()
    gpu_present = _gpu_present()

    fingerprint = {
        "cpu_arch": cpu_arch,
        "platform_id": platform_id,
        "mem_total_bytes": mem_total_bytes,
        "storage_class": storage_class,
        "gpu_present": gpu_present,
    }
    fingerprint["fingerprint_hash"] = sha256_hex(canonical_json(fingerprint))
    if run_ctx and run_ctx.get("now_utc"):
        fingerprint["now_utc"] = run_ctx["now_utc"]
    return fingerprint


def _platform_id() -> str:
    model_path = Path("/proc/device-tree/model")
    if model_path.exists():
        model = model_path.read_text(encoding="utf-8").strip("\x00")
        return model.lower().replace(" ", "-")
    return platform.platform().lower().replace(" ", "-")


def _mem_total_bytes() -> int:
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal"):
                parts = line.split()
                if len(parts) >= 2:
                    return int(parts[1]) * 1024
    return 0


def _storage_class() -> Optional[str]:
    if Path("/sys/block/nvme0n1").exists():
        return "nvme"
    if Path("/sys/block/mmcblk0").exists():
        return "sd"
    return None


def _gpu_present() -> bool:
    if Path("/proc/driver/nvidia/gpus").exists():
        return True
    if Path("/dev/nvhost-gpu").exists():
        return True
    return False
