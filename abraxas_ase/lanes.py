from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from .provenance import sha256_hex


@dataclass(frozen=True)
class LaneState:
    shadow: List[str]
    canary: List[str]
    core: List[str]
    shadow_count: int
    canary_count: int
    core_count: int
    lanes_sha256: str


def _read_txt(path: Path) -> List[str]:
    if not path.exists():
        return []
    lines = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip().lower()
        if not s or s.startswith("#"):
            continue
        if s.isalpha():
            lines.append(s)
    return sorted(set(lines))


def load_lane_files(lanes_dir: Path) -> LaneState:
    shadow = _read_txt(lanes_dir / "shadow.txt")
    canary = _read_txt(lanes_dir / "canary.txt")
    core = _read_txt(lanes_dir / "core.txt")

    payload = ("\n".join(shadow) + "\n||\n" + "\n".join(canary) + "\n||\n" + "\n".join(core) + "\n").encode("utf-8")
    lanes_hash = sha256_hex(payload)

    return LaneState(
        shadow=shadow,
        canary=canary,
        core=core,
        shadow_count=len(shadow),
        canary_count=len(canary),
        core_count=len(core),
        lanes_sha256=lanes_hash,
    )


def write_lane_file(path: Path, words: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sorted(set(words))) + "\n", encoding="utf-8", newline="\n")


def write_lane_files(lanes_dir: Path, *, shadow: List[str], canary: List[str], core: List[str]) -> LaneState:
    write_lane_file(lanes_dir / "shadow.txt", shadow)
    write_lane_file(lanes_dir / "canary.txt", canary)
    write_lane_file(lanes_dir / "core.txt", core)
    return load_lane_files(lanes_dir)
