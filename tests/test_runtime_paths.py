"""Guard for the single path authority.

These tests exist because path plumbing has already caused real failures in this repo:
tests wrote into the live ``out/`` tree, so a passing run mutated repository state and
the next run saw different input. Nothing could redirect that output, so nothing could
make such a test hermetic.

The contract: defaults are stable and inside the repo, overrides are validated rather
than coerced, and a path that escapes the root is refused instead of written.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from abraxas.paths import (
    RuntimePaths,
    find_repo_root,
    parse_env_bool,
    parse_env_path,
    runtime_paths,
)


@pytest.fixture
def clean_env(monkeypatch):
    """Remove every override so defaults are the thing under test."""
    for name in ("ABX_ROOT", "ABX_OUT_DIR", "ABX_CONTRACTS_DIR"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


# --------------------------------------------------------------------------
# defaults
# --------------------------------------------------------------------------


def test_repo_root_contains_the_project_marker() -> None:
    root = find_repo_root()
    assert (root / "pyproject.toml").is_file(), f"{root} is not the repository root"


def test_defaults_are_inside_the_repository(clean_env) -> None:
    paths = RuntimePaths.from_env()
    assert paths.root == find_repo_root()
    assert paths.out_dir == paths.root / "out"
    assert paths.contracts_dir == paths.root / "contracts"

    assert paths.contains(paths.out_dir)
    assert paths.contains(paths.contracts_dir)


def test_defaults_point_at_real_directories(clean_env) -> None:
    """A default that does not exist is a typo waiting to be written to."""
    paths = RuntimePaths.from_env()
    assert paths.out_dir.is_dir(), f"{paths.out_dir} does not exist"
    assert paths.contracts_dir.is_dir(), f"{paths.contracts_dir} does not exist"


def test_artifact_accessors_live_under_out(clean_env) -> None:
    paths = RuntimePaths.from_env()
    for candidate in (paths.registry_out_dir, paths.reports_out_dir):
        assert paths.is_output(candidate)
        assert paths.contains(candidate)


def test_runtime_paths_is_frozen_and_hashable(clean_env) -> None:
    """Frozen so it cannot drift mid-run; hashable so two runs compare as values."""
    paths = RuntimePaths.from_env()
    assert hash(paths) == hash(RuntimePaths.from_env())
    assert paths == RuntimePaths.from_env()

    with pytest.raises(Exception):
        paths.out_dir = Path("/tmp")  # type: ignore[misc]


def test_runtime_paths_helper_matches_from_env(clean_env) -> None:
    assert runtime_paths() == RuntimePaths.from_env()


# --------------------------------------------------------------------------
# env overrides: validated, never coerced
# --------------------------------------------------------------------------


def test_out_dir_override_is_respected(clean_env, tmp_path) -> None:
    override = tmp_path / "somewhere_else"
    override.mkdir()
    clean_env.setenv("ABX_OUT_DIR", str(override))

    paths = RuntimePaths.from_env()
    assert paths.out_dir == override.resolve()
    assert paths.root == find_repo_root(), "an out override must not move the root"


def test_root_override_moves_the_derived_defaults(clean_env, tmp_path) -> None:
    clean_env.setenv("ABX_ROOT", str(tmp_path))
    paths = RuntimePaths.from_env()
    assert paths.root == tmp_path.resolve()
    assert paths.out_dir == tmp_path.resolve() / "out"


def test_blank_override_is_rejected(clean_env) -> None:
    """A blank value must not quietly become the current directory."""
    clean_env.setenv("ABX_OUT_DIR", "   ")
    with pytest.raises(ValueError, match="ABX_OUT_DIR must not be blank"):
        RuntimePaths.from_env()


def test_blank_path_helper_is_rejected(clean_env) -> None:
    clean_env.setenv("ABX_OUT_DIR", "")
    with pytest.raises(ValueError):
        parse_env_path("ABX_OUT_DIR", default=Path("out"))


@pytest.mark.parametrize("value,expected", [("1", True), ("yes", True), ("on", True),
                                            ("TRUE", True), ("0", False),
                                            ("no", False), ("off", False),
                                            ("FALSE", False)])
def test_boolean_parsing_accepts_explicit_values(clean_env, value, expected) -> None:
    clean_env.setenv("ABX_STRICT_PATHS", value)
    assert parse_env_bool("ABX_STRICT_PATHS", default=not expected) is expected


def test_boolean_parsing_defaults_when_unset(clean_env) -> None:
    clean_env.delenv("ABX_STRICT_PATHS", raising=False)
    assert parse_env_bool("ABX_STRICT_PATHS", default=True) is True
    assert parse_env_bool("ABX_STRICT_PATHS", default=False) is False


def test_boolean_parsing_rejects_a_typo(clean_env) -> None:
    """The whole point: 'flase' must not read as False and become a fail-open default."""
    clean_env.setenv("ABX_STRICT_PATHS", "flase")
    with pytest.raises(ValueError, match="ABX_STRICT_PATHS"):
        parse_env_bool("ABX_STRICT_PATHS", default=True)


# --------------------------------------------------------------------------
# containment: refuse to escape the root
# --------------------------------------------------------------------------


def test_resolve_rejects_traversal_out_of_the_root(clean_env) -> None:
    paths = RuntimePaths.from_env()
    with pytest.raises(ValueError, match="escapes the repository root"):
        paths.resolve(paths.out_dir / ".." / ".." / "etc" / "passwd")


def test_resolve_rejects_an_absolute_path_outside_the_root(clean_env) -> None:
    paths = RuntimePaths.from_env()
    with pytest.raises(ValueError, match="escapes the repository root"):
        paths.resolve("/etc/passwd")


def test_resolve_accepts_a_path_inside_the_root(clean_env) -> None:
    paths = RuntimePaths.from_env()
    resolved = paths.resolve(paths.out_dir / "sub" / "artifact.json")
    assert resolved.is_relative_to(paths.root)
    assert paths.is_output(resolved)


def test_must_be_output_refuses_a_source_path(clean_env) -> None:
    """Writing outside out_dir means writing into source — never intended."""
    paths = RuntimePaths.from_env()
    with pytest.raises(ValueError, match="expected a path under"):
        paths.resolve(paths.root / "abraxas" / "paths.py", must_be_output=True)


def test_is_output_is_false_for_source_paths(clean_env) -> None:
    paths = RuntimePaths.from_env()
    assert not paths.is_output(paths.root / "abraxas")
    assert not paths.is_output(paths.contracts_dir)
    assert paths.is_output(paths.out_dir)
