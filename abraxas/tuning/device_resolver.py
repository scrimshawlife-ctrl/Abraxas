"""Device profile resolver for deterministic portfolio selection."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

from abraxas.tuning.device_profile_schema import DeviceProfile


def resolve_device_profile(
    fingerprint: Dict[str, object],
    profiles: Iterable[DeviceProfile],
) -> Optional[DeviceProfile]:
    candidates = match_profiles(fingerprint, profiles)
    if not candidates:
        return None
    return candidates[0]


def match_profiles(
    fingerprint: Dict[str, object],
    profiles: Iterable[DeviceProfile],
) -> List[DeviceProfile]:
    candidates = [profile for profile in profiles if _matches(profile, fingerprint)]
    candidates.sort(key=lambda profile: _sort_key(profile))
    return candidates


def _matches(profile: DeviceProfile, fingerprint: Dict[str, object]) -> bool:
    criteria = profile.match_criteria
    if not _match_list(criteria.cpu_arch, str(fingerprint.get("cpu_arch") or "")):
        return False
    if not _match_list(criteria.platform, str(fingerprint.get("platform_id") or "")):
        return False
    mem_max = criteria.mem_max_bytes
    if mem_max is not None and int(fingerprint.get("mem_total_bytes") or 0) > mem_max:
        return False
    storage_class = criteria.storage_class
    if storage_class and storage_class != "*":
        if storage_class != fingerprint.get("storage_class"):
            return False
    gpu_present = criteria.gpu_present
    if gpu_present is not None and bool(fingerprint.get("gpu_present")) is not gpu_present:
        return False
    return True


def _match_list(options: List[str], value: str) -> bool:
    if not options:
        return False
    if "*" in options:
        return True
    return value in options


def _specificity(profile: DeviceProfile) -> int:
    criteria = profile.match_criteria
    specificity = 0
    specificity += 0 if "*" in criteria.cpu_arch else 1
    specificity += 0 if "*" in criteria.platform else 1
    specificity += 0 if criteria.storage_class in (None, "*") else 1
    specificity += 0 if criteria.gpu_present is None else 1
    specificity += 0 if criteria.mem_max_bytes is None else 1
    return specificity


def _sort_key(profile: DeviceProfile) -> Tuple[int, int, str]:
    return (-_specificity(profile), int(profile.priority), profile.profile_id)
