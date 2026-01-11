from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .storage import StoragePaths, read_json, write_json


VALID_TIERS = ("psychonaut", "academic", "enterprise")


@dataclass
class UserConfig:
    name: str
    location_label: str
    tier: str
    admin: bool

    @staticmethod
    def default() -> "UserConfig":
        return UserConfig(
            name="Daniel",
            location_label="Los Angeles, CA",
            tier="psychonaut",
            admin=False,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "user.v0",
            "name": self.name,
            "location_label": self.location_label,
            "tier": self.tier,
            "admin": self.admin,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "UserConfig":
        tier = d.get("tier", "psychonaut")
        if tier not in VALID_TIERS:
            tier = "psychonaut"
        return UserConfig(
            name=d.get("name", "Daniel"),
            location_label=d.get("location_label", "Los Angeles, CA"),
            tier=tier,
            admin=bool(d.get("admin", False)),
        )


@dataclass
class OverlaysConfig:
    enabled: Dict[str, bool]

    @staticmethod
    def default() -> "OverlaysConfig":
        return OverlaysConfig(
            enabled={
                "aalmanac": True,
                "neon_genie": True,
                "semiotic_weather": True,
                "memetic_futurecast": True,
                "financials": True,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"schema": "overlays.v0", "enabled": dict(self.enabled)}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "OverlaysConfig":
        enabled = d.get("enabled") or {}
        if not isinstance(enabled, dict):
            enabled = {}
        # default false for unknown; do not allow implicit enable
        return OverlaysConfig(enabled={k: bool(v) for k, v in enabled.items()})


def load_user_config(paths: StoragePaths) -> UserConfig:
    p = paths.user_config_path()
    d = read_json(p)
    if not d:
        uc = UserConfig.default()
        write_json(p, uc.to_dict())
        return uc
    return UserConfig.from_dict(d)


def save_user_config(paths: StoragePaths, uc: UserConfig) -> None:
    write_json(paths.user_config_path(), uc.to_dict())


def load_overlays_config(paths: StoragePaths) -> OverlaysConfig:
    p = paths.overlays_config_path()
    d = read_json(p)
    if not d:
        oc = OverlaysConfig.default()
        write_json(p, oc.to_dict())
        return oc
    return OverlaysConfig.from_dict(d)


def save_overlays_config(paths: StoragePaths, oc: OverlaysConfig) -> None:
    write_json(paths.overlays_config_path(), oc.to_dict())
