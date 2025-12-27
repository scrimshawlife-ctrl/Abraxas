# Real health probes (v0.1) — pure-ish reads only

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, Optional


def disk_free_pct(path: str = "/") -> float:
    usage = shutil.disk_usage(path)
    if usage.total == 0:
        return 0.0
    return (usage.free / usage.total) * 100.0


def systemd_is_active(service: str) -> Optional[bool]:
    try:
        rc = subprocess.call(["systemctl", "is-active", "--quiet", service])
        return rc == 0
    except Exception:
        return None


def systemd_is_failed(service: str) -> Optional[bool]:
    try:
        rc = subprocess.call(["systemctl", "is-failed", "--quiet", service])
        return rc == 0
    except Exception:
        return None


def basic_health_state(
    daemon_service: str = "abraxas-daemon", disk_path: str = "/"
) -> Dict[str, Any]:
    return {
        "daemon_alive": systemd_is_active(daemon_service),
        "daemon_failed": systemd_is_failed(daemon_service),
        "disk_free_pct": disk_free_pct(disk_path),
    }
