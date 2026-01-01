"""Runtime configuration for Abraxas environments."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional
import os

Profile = Literal["orin", "dev"]

@dataclass(frozen=True)
class RuntimeConfig:
    """Immutable runtime configuration."""
    profile: Profile
    root: Path
    assets_dir: Path
    overlays_dir: Path
    state_dir: Path
    http_host: str
    http_port: int
    log_level: str
    concurrency: int

def detect_default_root() -> Path:
    """Detect default root directory (Orin-friendly)."""
    return Path(os.environ.get("ABX_ROOT", "/opt/aal/abraxas")).resolve()

def load_config(profile: Optional[str] = None) -> RuntimeConfig:
    """Load runtime configuration from environment and defaults."""
    prof: Profile = (profile or os.environ.get("ABX_PROFILE", "orin")).strip()  # type: ignore
    if prof not in ("orin", "dev"):
        prof = "orin"

    root = detect_default_root()
    assets_dir = Path(os.environ.get("ABX_ASSETS", str(root / "assets"))).resolve()
    overlays_dir = Path(os.environ.get("ABX_OVERLAYS", str(root / ".aal" / "overlays"))).resolve()
    state_dir = Path(os.environ.get("ABX_STATE", str(root / ".aal" / "state"))).resolve()

    http_host = os.environ.get("ABX_HOST", "0.0.0.0")
    http_port = int(os.environ.get("ABX_PORT", "8765"))

    if prof == "orin":
        log_level = os.environ.get("ABX_LOG", "INFO")
        concurrency = int(os.environ.get("ABX_CONCURRENCY", "1"))
    else:
        log_level = os.environ.get("ABX_LOG", "DEBUG")
        concurrency = int(os.environ.get("ABX_CONCURRENCY", "2"))

    return RuntimeConfig(
        profile=prof,
        root=root,
        assets_dir=assets_dir,
        overlays_dir=overlays_dir,
        state_dir=state_dir,
        http_host=http_host,
        http_port=http_port,
        log_level=log_level,
        concurrency=concurrency,
    )
