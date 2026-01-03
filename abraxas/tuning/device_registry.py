"""Device profile registry loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from abraxas.tuning.device_profile_schema import DeviceProfile


DEFAULT_REGISTRY_PATH = Path(".aal/tuning/device_profiles.json")


def load_device_profiles(path: Path | None = None) -> List[DeviceProfile]:
    path = path or DEFAULT_REGISTRY_PATH
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    profiles = [DeviceProfile(**entry) for entry in (payload.get("profiles") or [])]
    return sorted(profiles, key=lambda profile: profile.profile_id)


def write_device_profiles(profiles: List[DeviceProfile], path: Path | None = None) -> None:
    path = path or DEFAULT_REGISTRY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"profiles": [profile.canonical_payload() for profile in profiles]}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
