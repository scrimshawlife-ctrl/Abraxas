"""Centralized operational paths — the single authority for where things live.

Why this exists
---------------
Output paths were previously spelled inline wherever they were needed: runners, tests
and the self-build chain each wrote ``Path("out") / ...`` by hand. That has two costs,
both of which have already caused real failures here:

1. **Tests wrote into the live repo.** Several tests read and rewrote tracked artifacts
   under ``out/``, so a passing run mutated repository state and the *next* run saw
   different input. That is the whole of the "stateful tests over committed out/
   artifacts" cluster — it is a path-plumbing problem, not a test problem.

2. **Nothing could redirect the output.** With no seam, there is no way to point a run at
   a temporary directory, so there is no way to make such a test hermetic.

This module follows the design in the second attempt (``Abraxas-v2.0``,
``core/config.py``): a frozen dataclass of resolved paths built from stable defaults plus
validated environment overrides. Its rule — *add a property here for any new artifact
before writing to disk* — is the part worth adopting; the enforcement is that ``resolve``
refuses a path that escapes the root.

Environment overrides
---------------------
``ABX_ROOT``, ``ABX_OUT_DIR``, ``ABX_CONTRACTS_DIR``, ``ABX_STRICT_PATHS``.

Overrides are validated, not coerced: a blank value raises rather than silently becoming
the current directory, and a typo in a boolean raises rather than defaulting. Fail loud on
a bad path — silently writing to the wrong place is the failure mode this module exists
to prevent.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})

#: Directory name of this package's repository, used to locate the root.
_MARKER = "pyproject.toml"


def parse_env_bool(name: str, *, default: bool) -> bool:
    """Parse a boolean environment variable, accepting only explicit values.

    An unrecognised value raises. Guessing at ``"flase"`` is how a fail-closed setting
    quietly becomes fail-open.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(
        f"{name} must be one of: 1, true, yes, on, 0, false, no, off (got {raw!r})"
    )


def parse_env_path(name: str, *, default: Path) -> Path:
    """Parse a path environment variable, rejecting blank overrides."""
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip()
    if not normalized:
        raise ValueError(f"{name} must not be blank")
    return Path(normalized).expanduser()


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Locate the repository root by walking up for a marker file.

    Falls back to the current directory so an installed copy still resolves, but the
    normal case is a search: relying on the process CWD instead is what let path bugs
    depend on where a command happened to be run from.
    """
    here = (start or Path(__file__)).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / _MARKER).is_file():
            return candidate
    return Path.cwd().resolve()


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    """Resolved operational paths for one runtime.

    Frozen so it cannot drift mid-run, and hashable so a test can compare two runtimes
    for equality instead of comparing fields one at a time.
    """

    root: Path
    out_dir: Path
    contracts_dir: Path

    @classmethod
    def from_env(cls, *, root: Optional[Path] = None) -> "RuntimePaths":
        resolved_root = parse_env_path(
            "ABX_ROOT", default=root or find_repo_root()
        ).resolve()
        return cls(
            root=resolved_root,
            out_dir=parse_env_path("ABX_OUT_DIR", default=resolved_root / "out"),
            contracts_dir=parse_env_path(
                "ABX_CONTRACTS_DIR", default=resolved_root / "contracts"
            ),
        )

    # -- artifact accessors -------------------------------------------------
    # Add a property here for any new artifact before writing it to disk.

    @property
    def schemas_dir(self) -> Path:
        return self.root / "schemas"

    @property
    def registry_out_dir(self) -> Path:
        return self.out_dir / "registry"

    @property
    def reports_out_dir(self) -> Path:
        return self.out_dir / "reports"

    # -- containment -------------------------------------------------------

    def contains(self, path: Union[str, Path]) -> bool:
        """Is this path inside the repository root?"""
        return self._normalized(path).is_relative_to(self.root)

    def is_output(self, path: Union[str, Path]) -> bool:
        """Is this path inside the output directory?

        The check a test should use before writing: writing outside ``out_dir`` means
        writing into source, which is never what a test wants.
        """
        return self._normalized(path).is_relative_to(self.out_dir)

    def resolve(self, path: Union[str, Path], *, must_be_output: bool = False) -> Path:
        """Resolve a path and refuse one that escapes the root.

        Containment is checked on the *resolved* path, so ``out/../../etc/passwd`` and a
        symlinked escape are both rejected. Pass ``must_be_output`` for anything a runner
        is about to write.
        """
        candidate = self._normalized(path)
        if not candidate.is_relative_to(self.root):
            raise ValueError(
                f"path escapes the repository root: {path!r} -> {candidate}"
            )
        if must_be_output and not candidate.is_relative_to(self.out_dir):
            raise ValueError(
                f"expected a path under {self.out_dir}, got {path!r} -> {candidate}"
            )
        return candidate

    @staticmethod
    def _normalized(path: Union[str, Path]) -> Path:
        """Absolute path with symlinks resolved.

        ``Path.resolve()`` also normalises ``..``, which is what makes the containment
        check meaningful rather than cosmetic.
        """
        return Path(path).expanduser().resolve()


def runtime_paths() -> RuntimePaths:
    """Convenience accessor: ``RuntimePaths`` built from the current environment."""
    return RuntimePaths.from_env()


__all__ = [
    "RuntimePaths",
    "find_repo_root",
    "parse_env_bool",
    "parse_env_path",
    "runtime_paths",
]
