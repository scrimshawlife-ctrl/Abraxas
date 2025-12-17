from __future__ import annotations
import time
import urllib.request
import json
import subprocess
from typing import Any, Dict, Optional

from abx.util.logging import log, warn, err

def _get(url: str, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = r.read().decode("utf-8")
            return json.loads(data)
    except Exception:
        return None

def _systemctl_restart(unit: str) -> bool:
    try:
        subprocess.check_call(["systemctl", "restart", unit], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def watchdog_loop(
    ready_url: str,
    unit_name: str,
    interval_s: int = 5,
    fail_threshold: int = 3,
) -> None:
    fails = 0
    log("watchdog_start", ready_url=ready_url, unit=unit_name, interval_s=interval_s, fail_threshold=fail_threshold)
    while True:
        res = _get(ready_url)
        ok = bool(res and res.get("ok") is True)
        if ok:
            if fails:
                log("watchdog_recovered", fails=fails)
            fails = 0
        else:
            fails += 1
            warn("watchdog_unready", fails=fails, response=res)
            if fails >= fail_threshold:
                warn("watchdog_restart_attempt", unit=unit_name)
                did = _systemctl_restart(unit_name)
                if did:
                    log("watchdog_restart_ok", unit=unit_name)
                    fails = 0
                else:
                    err("watchdog_restart_failed", unit=unit_name)
        time.sleep(interval_s)
