"""ABX-DEVICE_PROFILE_RESOLVE rune operator."""

from __future__ import annotations

from typing import Any, Dict

from abraxas.tuning.device_registry import load_device_profiles
from abraxas.tuning.device_resolver import match_profiles


def apply_device_profile_resolve(
    *,
    fingerprint: Dict[str, Any],
    strict_execution: bool = True,
) -> Dict[str, Any]:
    profiles = load_device_profiles()
    matched = match_profiles(fingerprint, profiles)
    selected = matched[0] if matched else None
    return {
        "selected_profile": selected.model_dump() if selected else None,
        "profile_id": selected.profile_id if selected else None,
        "matched_profiles": [profile.profile_id for profile in matched],
    }
